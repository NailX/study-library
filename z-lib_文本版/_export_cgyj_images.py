import fitz, os
SRC = '/home/lilis/.hermes/cache/documents/doc_840741300379_炒股养家心法(高清彩色)解密 (菩萨戒子 整理) (z-library.sk, 1lib.sk, z-lib.sk)(1).pdf'
BOOK = '炒股养家心法 (菩萨戒子 整理)'
IMGDIR = f'/home/lilis/study-library/z-lib_文本版/_扫描页图/{BOOK}'
os.makedirs(IMGDIR, exist_ok=True)
d = fitz.open(SRC)
for i in range(len(d)):
    fp = f'{IMGDIR}/{i+1:04d}.jpg'
    if os.path.exists(fp):
        continue
    pix = d[i].get_pixmap(dpi=200)
    pix.save(fp, jpg_quality=85)
print('exported', len(d), 'pages ->', IMGDIR)
