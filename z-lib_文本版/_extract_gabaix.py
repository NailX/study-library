import fitz, re, sys
SRC='/home/lilis/.hermes/cache/documents/doc_76aec1d73a8e_Power Laws in Economics and Finance (Gabaix, Xavier) (z-library.sk, 1lib.sk, z-lib.sk)(1).pdf'
d=fitz.open(SRC)
t0=d[0].get_text()[:200]
print('pages:',d.page_count,'| p0 text:',repr(t0[:120]))
OUT='/home/lilis/study-library/z-lib_文本版/Power Laws in Economics and Finance (Xavier Gabaix).txt'
with open(OUT,'w',encoding='utf-8') as f:
    for i in range(d.page_count):
        f.write(f'===== 第 {i+1} 页 =====\n')
        f.write(d[i].get_text())
        f.write('\n')
import subprocess
print('bytes:',len(open(OUT,'rb').read()))
