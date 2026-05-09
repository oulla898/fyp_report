"""Check every URL in the references.bib file. Reports HTTP status per URL."""
import re
import ssl
import sys
import urllib.request
import urllib.error
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

BIB = r'c:\Users\oulla\Desktop\SQU\competetions\sumo robot\fyp\tamra-amr-project\reports\fyp-report\references\references.bib'

URL_RE = re.compile(r'https?://[^\s}, ]+')

UA = 'Mozilla/5.0 (compatible; LinkChecker/1.0)'

# Tolerate cert-hygiene issues (expired certs, missing intermediate CAs).
# We're checking that the page exists, not verifying TLS auth.
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def _clean(u: str) -> str:
    # Strip LaTeX-style escaping and trailing punctuation from extracted URLs.
    u = u.replace('\\_', '_').replace('\\&', '&').replace('\\#', '#').replace('\\%', '%')
    u = u.rstrip('.,);}')
    # If a backslash sneaks in (e.g. from \texttt{...}\foo), cut at it.
    if '\\' in u:
        u = u.split('\\', 1)[0]
    return u


def check(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
            return url, resp.status, resp.url
    except urllib.error.HTTPError as e:
        if e.code in (403, 405):
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
                    return url, resp.status, resp.url
            except Exception as e2:
                return url, f'GET_ERR {type(e2).__name__}: {e2}', None
        return url, f'HTTP {e.code}', None
    except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
        return url, f'ERR {type(e).__name__}: {e}', None


def main():
    with open(BIB, encoding='utf-8') as f:
        text = f.read()

    bib_keys = {}
    current = None
    for line in text.splitlines():
        m = re.match(r'\s*@\w+\{(\w[\w:\.]+),', line)
        if m:
            current = m.group(1)
            continue
        for u in URL_RE.findall(line):
            u = _clean(u)
            if u:
                bib_keys.setdefault(u, []).append(current or '?')

    urls = list(bib_keys)
    print(f'Found {len(urls)} unique URLs to check.\n')

    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(check, u): u for u in urls}
        for fut in as_completed(futs):
            url, status, final = fut.result()
            ok = isinstance(status, int) and 200 <= status < 400
            results.append((ok, url, status, final, bib_keys[url]))

    results.sort(key=lambda r: (r[0], r[1]))

    print('=== BROKEN / SUSPICIOUS ===')
    for ok, url, status, final, keys in results:
        if not ok:
            print(f'  [{status}] {url}')
            print(f'    cited by: {", ".join(keys)}')

    print('\n=== OK ===')
    for ok, url, status, final, keys in results:
        if ok:
            redir = f' -> {final}' if final and final != url else ''
            print(f'  [{status}] {url}{redir}')

    bad = sum(1 for r in results if not r[0])
    print(f'\nTotal: {len(results)} URLs | {bad} broken/error')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
