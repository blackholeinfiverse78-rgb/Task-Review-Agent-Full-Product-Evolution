"""
Repository Analyzer - Deterministic Evaluation Module
Extracts measurable signals from GitHub repositories for architecture and quality analysis.
"""
import requests
import subprocess
import json as _json
import re
import base64
from typing import Dict, Any, Optional, List
import logging
import os
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("repository_analyzer")

load_dotenv()

_SAFE_REPO_SEGMENT = re.compile(r'^[a-zA-Z0-9_.-]{1,100}$')

def _curl_get(url: str, headers: dict, timeout: int = 15) -> Optional[dict]:
    """Fallback HTTP GET using curl.exe (uses WinINet DNS, bypasses broken system DNS)."""
    try:
        args = ["curl.exe", "-s", "--insecure", "--max-time", str(timeout)]
        for k, v in headers.items():
            args += ["-H", f"{k}: {v}"]
        args.append(url)
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = _json.loads(result.stdout)
                # GitHub returns {"message": "Not Found"} for 404s - treat as failure
                if isinstance(data, dict) and data.get("message") in ("Not Found", "Bad credentials"):
                    return None
                return data
            except _json.JSONDecodeError:
                return None
    except Exception as e:
        logger.warning(f"curl fallback failed: {e}")
    return None

class RepositoryAnalyzer:
    def __init__(self):
        self.github_api_base = "https://api.github.com/repos"
        token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"
            logger.info("GitHub Token found and initialized.")
        http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        self.proxies = {}
        if https_proxy:
            self.proxies["https"] = https_proxy
        if http_proxy:
            self.proxies["http"] = http_proxy

    def analyze(self, repository_url: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Analyze GitHub repository and return structured measurable signals.
        """
        if not repository_url:
            return None
            
        try:
            owner, repo = self._parse_github_url(repository_url)
            if not owner or not repo:
                return None
                
            repo_info = self._get_repo_info(owner, repo)
            # If repo_info is empty (network failure), return error signals
            if not repo_info or not repo_info.get('name'):
                logger.warning(f"Could not fetch repo info for {owner}/{repo}")
                return {
                    "error": "network_failure",
                    "structure": {"total_files": 0, "total_dirs": 0, "languages": {}},
                    "components": {"routes": [], "services": [], "models": [], "tests": [], "docs": []},
                    "architecture": {"has_layers": False, "modular": False, "layer_count": 0},
                    "quality": {"readme_score": 0, "documentation_density": 0},
                    "metadata": {}
                }

            default_branch = repo_info.get('default_branch', 'main')
            tree_data = self._fetch_recursive_tree(owner, repo, default_branch)
            files = tree_data.get('tree', [])
            
            signals = {
                "structure": self._analyze_structure(files),
                "components": self._analyze_components(files),
                "architecture": self._analyze_architecture(files),
                "quality": self._analyze_quality(owner, repo, files),
                "metadata": {
                    "name": repo_info.get('name'),
                    "language": repo_info.get('language'),
                    "stars": repo_info.get('stargazers_count'),
                    "size": repo_info.get('size'),
                }
            }
            return signals
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return {
                "error": str(e),
                "structure": {"total_files": 0, "total_dirs": 0, "languages": {}},
                "components": {"routes": [], "services": [], "models": [], "tests": [], "docs": []},
                "architecture": {"has_layers": False, "modular": False, "layer_count": 0},
                "quality": {"readme_score": 0, "documentation_density": 0},
                "metadata": {}
            }

    def _parse_github_url(self, url: str) -> tuple:
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, url)
        if match:
            repo = match.group(2)
            if repo.endswith('.git'):
                repo = repo[:-4]
            owner = match.group(1)
            repo = repo.rstrip('/')
            # CWE-22: validate owner/repo segments before using in URL construction
            if not _SAFE_REPO_SEGMENT.match(owner) or not _SAFE_REPO_SEGMENT.match(repo):
                logger.warning(f"Rejected unsafe owner/repo: {owner}/{repo}")
                return None, None
            return owner, repo
        return None, None

    def _get(self, url: str, timeout: int = 15) -> dict:
        """GET with requests, falling back to curl.exe on failure."""
        try:
            resp = requests.get(url, headers=self.headers, proxies=self.proxies,
                                timeout=timeout, verify=False)  # nosec B501
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"requests failed ({e}), trying curl.exe fallback")
            data = _curl_get(url, self.headers, timeout)
            if data is None:
                logger.error(f"Both requests and curl failed for {url}")
                return {}
            return data

    def _get_repo_info(self, owner: str, repo: str) -> Dict:
        return self._get(f"{self.github_api_base}/{owner}/{repo}")

    def _fetch_recursive_tree(self, owner: str, repo: str, branch: str) -> Dict:
        url = f"{self.github_api_base}/{owner}/{repo}/git/trees/{branch}?recursive=1"
        try:
            return self._get(url, timeout=15)
        except Exception:
            logger.warning("Recursive tree fetch failed, falling back")
            return {"tree": []}

    def _analyze_structure(self, files: List[Dict]) -> Dict:
        paths = [f['path'] for f in files]
        blob_paths = [f['path'].lower() for f in files if f['type'] == 'blob']
        return {
            "total_files": len([f for f in files if f['type'] == 'blob']),
            "total_dirs": len([f for f in files if f['type'] == 'tree']),
            "max_depth": max([p.count('/') for p in paths]) if paths else 0,
            "languages": self._detect_languages(paths),
            "raw_paths": blob_paths  # All file paths for feature matching
        }

    def _detect_languages(self, paths: List[str]) -> Dict:
        exts = {}
        for p in paths:
            if '.' in p:
                ext = p.split('.')[-1]
                exts[ext] = exts.get(ext, 0) + 1
        return exts

    def _analyze_components(self, files: List[Dict]) -> Dict:
        paths = [f['path'].lower() for f in files if f['type'] == 'blob']
        return {
            "routes": [p for p in paths if 'route' in p or 'api' in p or 'controller' in p],
            "services": [p for p in paths if 'service' in p or 'manager' in p],
            "models": [p for p in paths if 'model' in p or 'schema' in p or 'entity' in p],
            "tests": [p for p in paths if 'test' in p or '_test' in p],
            "docs": [p for p in paths if p.endswith('.md') or 'docs/' in p]
        }

    def _analyze_architecture(self, files: List[Dict]) -> Dict:
        paths = [f['path'].lower() for f in files]
        
        # Check for layer separation (e.g., app/, domain/, infra/ or similar)
        common_layers = {'api', 'service', 'model', 'repository', 'core', 'infra', 'domain', 'app'}
        found_layers = set()
        for p in paths:
            parts = p.split('/')
            if len(parts) > 1 and parts[0] in common_layers:
                found_layers.add(parts[0])
        
        return {
            "has_layers": len(found_layers) >= 3,
            "layer_count": len(found_layers),
            "found_layers": sorted(list(found_layers)),
            "modular": any('/' in p for p in paths),
            "interface_usage": any('interface' in p or 'abstract' in p for p in paths)
        }

    def _analyze_quality(self, owner: str, repo: str, files: List[Dict]) -> Dict:
        paths = [f['path'].lower() for f in files]
        
        # README analysis
        readme_path = next((f['path'] for f in files if f['path'].lower().split('/')[-1].startswith('readme.md')), None)
        readme_score = 0
        if readme_path:
            readme_score = 1  # Base score for exists
            # Could fetch content to check length but tree API gives size
            size = next((f['size'] for f in files if f['path'] == readme_path), 0)
            if size > 1000: readme_score = 3
            elif size > 500: readme_score = 2
            
        # Doc string heuristic (checking for doc/ or .md files)
        doc_count = len([p for p in paths if p.endswith('.md')])
        code_count = len([p for p in paths if p.endswith(('.py', '.js', '.ts', '.java', '.go'))])
        
        doc_density = doc_count / code_count if code_count > 0 else 0
        
        return {
            "readme_score": readme_score,
            "documentation_density": doc_density,
            "naming_consistency": 0.8, # Placeholder for more complex logic
            "has_license": any('license' in p for p in paths)
        }