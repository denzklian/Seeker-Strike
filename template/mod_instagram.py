#!/usr/bin/env python3
import os
import utils

R = '\033[31m'
G = '\033[32m'
C = '\033[36m'
W = '\033[0m'

with open('template/instagram/index_temp.html', 'r', encoding='utf-8') as temp_index:
    temp_index_data = temp_index.read()
    if os.getenv("DEBUG_HTTP") == "1":
        temp_index_data = temp_index_data.replace('window.location = "https:" + restOfUrl;', '')

with open('template/instagram/index.html', 'w', encoding='utf-8') as updated_index:
    updated_index.write(temp_index_data)
