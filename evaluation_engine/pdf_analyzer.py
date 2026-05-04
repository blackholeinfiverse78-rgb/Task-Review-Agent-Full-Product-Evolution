"""
PDF Analyzer - Deterministic PDF Parsing and Analysis
Extracts and analyzes PDF content for task evaluation.
"""
import io
import os
import re
import logging
import pdfplumber
from typing import Dict, Any, List, Optional
from fastapi import UploadFile, HTTPException

logger = logging.getLogger("pdf_analyzer")

_SAFE_FILENAME_RE = re.compile(r'[^a-zA-Z0-9._-]')
_MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB

class PDFAnalyzer:
    def __init__(self, upload_dir: str = "storage/uploads"):
        self.upload_dir = upload_dir
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)
            
        # Analysis keywords
        self.stack_keywords = {
            'python', 'javascript', 'typescript', 'fastapi', 'flask', 'django',
            'react', 'vue', 'angular', 'node', 'express', 'postgresql', 'sql',
            'mongodb', 'nosql', 'docker', 'kubernetes', 'aws', 'azure', 'gcp'
        }

    def process_upload(self, file: UploadFile) -> Dict[str, Any]:
        """
        Handles PDF upload, storage, and text extraction.
        """
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        # CWE-22: Sanitize filename — strip path components and unsafe chars
        safe_name = _SAFE_FILENAME_RE.sub('_', os.path.basename(file.filename))[:100]
        file_path = os.path.join(self.upload_dir, f"{os.urandom(8).hex()}_{safe_name}")
        # Ensure resolved path stays within upload_dir
        if not os.path.realpath(file_path).startswith(os.path.realpath(self.upload_dir)):
            raise HTTPException(status_code=400, detail="Invalid file path.")

        try:
            content = file.file.read(_MAX_PDF_SIZE + 1)
            if len(content) > _MAX_PDF_SIZE:
                raise HTTPException(status_code=413, detail="PDF exceeds 10 MB limit.")
            with open(file_path, "wb") as f:
                f.write(content)
            file.file.seek(0)
        except HTTPException:
            raise
        except OSError as e:
            logger.error(f"Failed to save PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to store the PDF file.")

        # 2. Extract Text
        extracted_text = self.extract_text(content)
        
        # 3. Analyze Content
        analysis = self.analyze_content(extracted_text)
        
        return {
            "file_path": file_path,
            "extracted_text": extracted_text,
            "analysis": analysis
        }

    def extract_text(self, content: bytes) -> str:
        """
        Extracts clean text from PDF bytes.
        """
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                return "\n\n".join(pages).strip()
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ""

    def analyze_content(self, text: str) -> Dict[str, Any]:
        """
        Deterministic analysis of PDF text.
        """
        if not text:
            return {
                "documented_features": [],
                "architecture_description": "No documentation detected",
                "technical_stack": [],
                "implementation_steps": []
            }

        text_lower = text.lower()
        
        # 1. Technical Stack Discovery
        found_stack = [word for word in self.stack_keywords if word in text_lower]
        
        # 2. Section Based Detection (Heuristic)
        # Look for headers like 'Features', 'Architecture', 'Overview', 'Steps'
        features = []
        feature_match = re.search(r'(?i)(features|objectives|requirements)[\s\S]*?(?=\n\n|\n[A-Z]|$)', text)
        if feature_match:
            # Basic bullet point extraction
            features = [f.strip(' -*•') for f in feature_match.group(0).split('\n')[1:] if f.strip()]

        arch_summary = "General architecture described"
        arch_match = re.search(r'(?i)(architecture|design|structure)[\s\S]*?(?=\n\n|\n[A-Z]|$)', text)
        if arch_match:
            lines = arch_match.group(0).split('\n')[1:4] # Get first few lines
            arch_summary = " ".join([l.strip() for l in lines if l.strip()])[:200]

        return {
            "documented_features": features[:10],
            "architecture_description": arch_summary,
            "technical_stack": found_stack,
            "implementation_steps": [] # Future expansion
        }
