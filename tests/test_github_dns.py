import socket
import dns.resolver as _dns_resolver
_resolver = _dns_resolver.Resolver(configure=False)
_resolver.nameservers = ['8.8.8.8', '8.8.4.4']
_resolver.timeout = 3
_resolver.lifetime = 5
_dns_cache = {}
_original_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host and not host.replace('.','').isdigit() and host not in ('localhost','127.0.0.1'):
        if host not in _dns_cache:
            try:
                answers = _resolver.resolve(host, 'A')
                _dns_cache[host] = str(answers[0])
            except Exception:
                pass
        if host in _dns_cache:
            return _original_getaddrinfo(_dns_cache[host], port, family, type, proto, flags)
    return _original_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _patched_getaddrinfo

if __name__ == "__main__":
    import requests, os
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    print('Token loaded:', bool(token))
    resp = requests.get(
        'https://api.github.com/repos/octocat/Hello-World',
        headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'},
        timeout=15
    )
    print('Status:', resp.status_code)
    print('Repo:', resp.json().get('name'))
    print('Rate limit remaining:', resp.headers.get('X-RateLimit-Remaining'))
