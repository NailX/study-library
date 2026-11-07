import fitz, re
SRC = '/home/lilis/.hermes/cache/documents/doc_a23897c565de_Statistical Consequences of Fat Tails Real World Preasymptotics, Epistemology, and Applications (Nassim Nicholas Taleb) (z-library.sk, 1lib.sk, z-lib.sk)(1).pdf'
OUT = '/home/lilis/study-library/z-lib_文本版/Statistical Consequences of Fat Tails (Nassim Nicholas Taleb).txt'
d = fitz.open(SRC)
with open(OUT, 'w', encoding='utf-8') as f:
    for i in range(d.page_count):
        t = d[i].get_text()
        t = re.sub(r'\n{3,}', '\n\n', t)
        f.write(f'===== 第 {i+1} 页 =====\n{t}\n')
import os
print('pages:', d.page_count, '| bytes:', os.path.getsize(OUT))
