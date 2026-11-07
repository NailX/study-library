import fitz
SRC='/home/lilis/.hermes/cache/documents/doc_70953ed6943b_A theory of power-law distributions in financial market fluctuations (Gabaix, Xavier Gopikrishnan etc.) (z-library.sk, 1lib.sk, z-lib.sk)(1).pdf'
d=fitz.open(SRC)
print('pages:',d.page_count,'| p0:',repr(d[0].get_text()[:100]))
OUT='/home/lilis/study-library/z-lib_文本版/A Theory of Power-Law Distributions in Financial Market Fluctuations (Gabaix Gopikrishnan Plerou Stanley).txt'
with open(OUT,'w',encoding='utf-8') as f:
    for i in range(d.page_count):
        f.write(f'===== 第 {i+1} 页 =====\n'); f.write(d[i].get_text()); f.write('\n')
print('bytes:',len(open(OUT,'rb').read()))
