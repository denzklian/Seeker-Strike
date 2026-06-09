#!/usr/bin/env python3
import sys
import utils
import requests

R = '\033[31m'
G = '\033[32m'
C = '\033[36m'
W = '\033[0m'
Y = '\033[33m'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36'
}


def _safe_get(url, params=None, timeout=10):
    try:
        s = requests.Session()
        s.headers.update(HEADERS)
        rqst = s.get(url, params=params, timeout=timeout)
        return rqst.status_code, rqst.text.strip()
    except Exception:
        return None, None


def shorten_tinyurl(long_url):
    try:
        code, text = _safe_get('https://tinyurl.com/api-create.php', {'url': long_url})
        if code == 200 and text and text.startswith('http'):
            return text, None
        return None, (text or 'Unknown error')[:200]
    except Exception as e:
        return None, str(e)


def shorten_isgd(long_url):
    try:
        code, text = _safe_get('https://is.gd/create.php', {'format': 'simple', 'url': long_url})
        if code == 200 and text and text.startswith('http'):
            return text, None
        return None, (text or 'Unknown error')[:200]
    except Exception as e:
        return None, str(e)


def shorten_vgd(long_url):
    try:
        code, text = _safe_get('https://v.gd/create.php', {'format': 'simple', 'url': long_url})
        if code == 200 and text and text.startswith('http'):
            return text, None
        return None, (text or 'Unknown error')[:200]
    except Exception as e:
        return None, str(e)


def shorten_dagd(long_url):
    try:
        code, text = _safe_get('https://da.gd/s', {'url': long_url})
        if code == 200 and text and text.startswith('http'):
            return text, None
        return None, (text or 'Unknown error')[:200]
    except Exception as e:
        return None, str(e)


def shorten_cleanuri(long_url):
    try:
        rqst = requests.post(
            'https://cleanuri.com/api/v1/shorten',
            data={'url': long_url},
            headers=HEADERS,
            timeout=10,
        )
        if rqst.status_code == 200:
            data = rqst.json()
            result = data.get('result_url')
            if result:
                return result, None
        return None, rqst.text.strip()[:200]
    except Exception as e:
        return None, str(e)


def shorten_1pt(long_url):
    try:
        rqst = requests.post(
            'https://csclub.uwaterloo.ca/~phthakka/1pt-express/addURL',
            data={'long': long_url},
            headers=HEADERS,
            timeout=10,
        )
        if rqst.status_code == 200 and rqst.text.strip().startswith('http'):
            return rqst.text.strip(), None
        return None, rqst.text.strip()[:200]
    except Exception as e:
        return None, str(e)


def shorten_chilpit(long_url):
    try:
        rqst = requests.post(
            'https://chilp.it/api.php',
            data={'url': long_url},
            headers=HEADERS,
            timeout=10,
        )
        if rqst.status_code == 200 and rqst.text.strip().startswith('http'):
            return rqst.text.strip(), None
        return None, rqst.text.strip()[:200]
    except Exception as e:
        return None, str(e)


def shorten(long_url):
    if not long_url.startswith('http'):
        return None, 'URL must start with http:// or https://'

    utils.print(f'{G}[+] {C}Shortening URL...{W}')

    services = [
        ('TinyURL', shorten_tinyurl),
        ('is.gd', shorten_isgd),
        ('v.gd', shorten_vgd),
        ('chilp.it', shorten_chilpit),
        ('cleanuri', shorten_cleanuri),
        ('1pt.co', shorten_1pt),
        ('da.gd', shorten_dagd),
    ]

    for name, func in services:
        result, error = func(long_url)
        if result:
            utils.print(f'{G}[+] {C}Shortened via {name}: {W}{result}')
            return result, None
        utils.print(f'{Y}[!] {C}{name} error: {W}{error}')

    return None, 'All shortening services failed'


def main():
    print(f'''
{Y}╔══════════════════════════════════════╗
║     Seeker URL Shortener Utility     ║
╚══════════════════════════════════════╝{W}
''')

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input(f'{G}[>] {C}Enter URL to shorten: {W}').strip()

    if not url:
        utils.print(f'{R}[-] {C}No URL provided{W}')
        sys.exit(1)

    result, error = shorten(url)
    if result:
        utils.print(f'\n{G}[+] {C}Short URL: {W}{result}')
        try:
            import pyperclip
            pyperclip.copy(result)
            utils.print(f'{G}[+] {C}Copied to clipboard!{W}')
        except ImportError:
            pass
    else:
        utils.print(f'\n{R}[-] {C}Failed: {W}{error}')
        sys.exit(1)


if __name__ == '__main__':
    main()
