#!/usr/bin/env python3
import sys, os, json, requests, re, subprocess, time

R = '\033[31m'
G = '\033[32m'
C = '\033[36m'
W = '\033[0m'
Y = '\033[33m'


def sanitize_subdomain(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    if not name:
        name = 'seeker'
    return name


def deploy_worker(api_token, account_id, script_name, script_content):
    headers = {'Authorization': f'Bearer {api_token}'}
    metadata = {'body_part': 'script', 'bindings': []}
    upload_data = {
        'metadata': (None, json.dumps(metadata), 'application/json'),
        'script': (script_name, script_content, 'application/javascript'),
    }
    resp = requests.put(
        f'https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}',
        headers=headers,
        files=upload_data,
    )
    return resp


def verify_worker(worker_url, max_retries=6):
    for i in range(max_retries):
        try:
            r = requests.get(worker_url, timeout=8)
            if r.status_code in (200, 301, 302):
                body = r.text[:500].lower()
                if 'cloudflare workers' in body or 'error code' in body:
                    return False, 'Worker returned error page'
                return True, None
            return False, f'HTTP {r.status_code}'
        except requests.ConnectionError:
            pass
        except Exception as e:
            return False, str(e)
        time.sleep(1.5)
    return False, 'Worker not reachable'


def main():
    dotenv_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.env')
    if os.path.exists(dotenv_path):
        with open(dotenv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

    api_token = None
    tunnel_url = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--api-token' and i + 1 < len(sys.argv):
            api_token = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == '--tunnel-url' and i + 1 < len(sys.argv):
            tunnel_url = sys.argv[i + 1]
            i += 1
        i += 1

    if not api_token:
        api_token = os.getenv('CF_API_TOKEN')

    if not api_token:
        print(f'{Y}[!] {C}Cloudflare API Token dibutuhkan.{W}')
        print(f'{C}Cara buat token:{W}')
        print(f'  1. Buka https://dash.cloudflare.com/profile/api-tokens')
        print(f'  2. Klik "Create Token" > "Edit Cloudflare Workers"')
        print(f'  3. Copy token nya')
        print()
        api_token = input(f'{G}[>] {C}API Token: {W}').strip()

    if not tunnel_url:
        tunnel_url = input(f'{G}[>] {C}Tunnel URL (https://xxx.ngrok-free.app): {W}').strip()

    if not tunnel_url.startswith('http'):
        tunnel_url = 'https://' + tunnel_url
    if tunnel_url.endswith('/'):
        tunnel_url = tunnel_url.rstrip('/')

    print(f'\n{G}[+] {C}Deploy Worker dengan tunnel: {W}{tunnel_url}')

    worker_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cloudflare-worker.js')
    if not os.path.exists(worker_path):
        print(f'{R}[-] {C}cloudflare-worker.js tidak ditemukan!{W}')
        sys.exit(1)

    with open(worker_path, 'r') as f:
        script_content = f.read()

    script_content = script_content.replace('https://YOUR_TUNNEL_URL.lhr.life', tunnel_url)

    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}

    print(f'{G}[+] {C}Mengambil akun Cloudflare...{W}')
    resp = requests.get('https://api.cloudflare.com/client/v4/accounts', headers=headers)
    if resp.status_code != 200:
        print(f'{R}[-] {C}Gagal fetch akun: {W}{resp.text[:200]}')
        sys.exit(1)

    accounts = resp.json().get('result', [])
    if not accounts:
        print(f'{R}[-] {C}Tidak ada akun Cloudflare ditemukan{W}')
        sys.exit(1)

    account_id = accounts[0]['id']
    account_name = accounts[0]['name']
    print(f'{G}[+] {C}Akun: {W}{account_name} ({account_id[:12]}...)')

    print(f'{G}[+] {C}Mengambil workers.dev subdomain...{W}')
    sub_resp = requests.get(
        f'https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/subdomain',
        headers={'Authorization': f'Bearer {api_token}'}
    )
    if sub_resp.status_code == 200:
        sub_data = sub_resp.json().get('result', {})
        subdomain = sub_data.get('subdomain', '')
        if not subdomain:
            subdomain = sanitize_subdomain(account_name)
    else:
        subdomain = sanitize_subdomain(account_name)

    script_name = 'seeker-proxy'
    worker_url = f'https://{script_name}.{subdomain}.workers.dev'

    print(f'{G}[+] {C}Upload worker...{W}', end='')
    resp = deploy_worker(api_token, account_id, script_name, script_content)

    if resp.status_code in (200, 201):
        print(f'{C}[ {G}OK{C} ]{W}')
    else:
        print(f'{C}[ {R}FAIL{C} ]{W}')
        print(f'{R}[-] {C}Deploy error: {W}{resp.text[:300]}')
        sys.exit(1)

    print(f'{G}[+] {C}Enable workers.dev subdomain...{W}', end='')
    enable_resp = requests.post(
        f'https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}/subdomain',
        headers={'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'},
        json={'enabled': True}
    )
    if enable_resp.status_code == 200 and enable_resp.json().get('success'):
        print(f'{C}[ {G}OK{C} ]{W}')
    else:
        print(f'{C}[ {Y}SKIP{C} ]{W}')

    print(f'{G}[+] {C}Verifikasi worker...{W}', end='', flush=True)
    time.sleep(3)
    ok, err = verify_worker(worker_url)

    if ok:
        print(f'{C}[ {G}OK{C} ]{W}')
    else:
        print(f'{C}[ {Y}WARN{C} ]{W}')
        print(f'{Y}[!] {C}Warning: {err}. Worker mungkin butuh waktu deploy.{W}')

    print(f'\n{G}[+] {C}Worker berhasil di-deploy!{W}')
    print(f'{G}[+] {C}URL Worker: {W}{worker_url}')
    print(f'\n{Y}[!] {C}CARA PAKAI:{W}')
    print(f'  1. Kirim URL di atas ke target ({worker_url})')
    print(f'  2. Semua request diteruskan ke tunnel ({tunnel_url})')
    print(f'  3. Bisa dishorten dengan: python seeker.py -s {worker_url}')
    print(f'\n{Y}[!] {C}NOTE: Setiap kali tunnel URL berubah, deploy ulang:{W}')
    print(f'  python deploy_cf.py --tunnel-url https://URL_BARU')
    print()

    print(f'WORKER_URL={worker_url}')


if __name__ == '__main__':
    main()
