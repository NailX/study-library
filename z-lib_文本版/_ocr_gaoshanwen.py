#!/usr/bin/env python3
# 扫描版PDF → 页图(200dpi jpg) → 包装单页PDF → PaddleOCR-VL → 每页文本
# 页级幂等 resume：输出 txt 里已有 ===== 第 N 页 ===== 的跳过；失败标记会重试
import fitz, requests, os, re, io, json, time, sys, threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

BASE = '/home/lilis/study-library/z-lib_文本版'
PDFS = {
    '透视繁荣': '/home/lilis/.hermes/cache/documents/doc_7ba918fc25a9_透视繁荣：资产重估深处的忧虑 (高善文主编, 高善文著, 高善文) (z-library.sk, 1lib.sk, z-lib.sk).pdf',
    '经济的运行逻辑': '/home/lilis/.hermes/cache/documents/doc_950c12a116f8_经济的运行逻辑 (高善文著) (z-library.sk, 1lib.sk, z-lib.sk).pdf',
}
PAGEDIR = os.path.join(BASE, '_pages_高善文')
os.makedirs(PAGEDIR, exist_ok=True)

TOKEN = os.environ.get('PADDLEOCR_TOKEN', 'cd12d7e34f91551950fbfe624ab657588eb46129')
JOB = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
AUTH = {"Authorization": f"token {TOKEN}"}
lock = threading.Lock()
_stats = {'ok': 0, 'fail': 0}


def ocr_image(data):
    # API 仅可靠识别 PDF：图片先包装成单页PDF再上传
    try:
        img = Image.open(io.BytesIO(data)).convert('RGB')
        buf = io.BytesIO()
        img.save(buf, 'PDF', resolution=150)
        pdf = buf.getvalue()
    except Exception as e:
        return f'[PDF_WRAP_ERR {e}]'
    try:
        r = requests.post(JOB, files={'file': ('page.pdf', pdf, 'application/pdf')},
                          data={'model': 'PaddleOCR-VL-1.6', 'fileType': '1'}, headers=AUTH, timeout=90)
        if r.status_code != 200:
            return f'[OCR_FAIL HTTP {r.status_code}]'
        jid = r.json()['data']['jobId']
    except Exception as e:
        return f'[OCR_ERR {e}]'
    for _ in range(150):
        try:
            d = requests.get(f"{JOB}/{jid}", headers=AUTH, timeout=30).json().get('data', {})
            if d.get('state') == 'done':
                txt = ''
                for attempt in range(6):
                    try:
                        txt = requests.get(d['resultUrl']['jsonUrl'], timeout=30).text
                    except Exception:
                        txt = ''
                    if txt.strip():
                        break
                    time.sleep(2)
                if not txt.strip():
                    return '[OCR_EMPTY_URL]'
                parts = []
                try:
                    o = json.loads(txt)
                    res = o['result']['layoutParsingResults'][0]['prunedResult']['parsing_res_list']
                    parts = [b['block_content'].strip() for b in res if b.get('block_content', '').strip()]
                except Exception:
                    for line in txt.split('\n'):
                        try:
                            o = json.loads(line.strip().rstrip(','))
                            for b in o['result']['layoutParsingResults'][0]['prunedResult']['parsing_res_list']:
                                c = (b.get('block_content') or '').strip()
                                if c:
                                    parts.append(c)
                        except Exception:
                            pass
                return '\n'.join(parts) if parts else '[OCR_EMPTY]'
            if d.get('state') in ('failed', 'error'):
                return '[OCR_JOB_FAIL]'
        except Exception:
            pass
        time.sleep(2)
    return '[OCR_TIMEOUT]'


def export_pages(pdf, tag):
    doc = fitz.open(pdf)
    fps = []
    for i, page in enumerate(doc, 1):
        fp = os.path.join(PAGEDIR, f'{tag}_{i:04d}.jpg')
        if not os.path.exists(fp):
            pix = page.get_pixmap(dpi=200)
            pix.save(fp, jpg_quality=85)
        fps.append(fp)
    doc.close()
    return fps


def process(tag, pdf):
    outfp = os.path.join(BASE, f'{tag}.pdf.txt')
    pages = export_pages(pdf, tag)
    done = set()
    if os.path.exists(outfp):
        content = open(outfp, encoding='utf-8').read()
        for m in re.finditer(r'===== 第 (\d+) 页 =====\n(.*?)(?=^===== 第 |\Z)', content, re.M | re.S):
            body = m.group(2).strip()
            if body and not body.startswith('[OCR_') and not body.startswith('[PDF'):
                done.add(int(m.group(1)))
    todo = [p for p in pages if int(re.search(r'_(\d+)\.jpg$', p).group(1)) not in done]
    print(f"[{tag}] 共{len(pages)}页 待OCR {len(todo)}", flush=True)
    if not todo:
        return

    def one(fp):
        n = int(re.search(r'_(\d+)\.jpg$', fp).group(1))
        try:
            data = open(fp, 'rb').read()
            txt = ocr_image(data)
            # 失败重试一次（原图）
            if txt.startswith('[OCR_'):
                time.sleep(2)
                txt = ocr_image(data)
        except Exception as e:
            txt = f'[READ_FAIL {e}]'
        return n, txt

    results = {}
    with ThreadPoolExecutor(4) as ex:
        futs = {ex.submit(one, p): p for p in todo}
        done_n = 0
        for fu in futs:
            n, txt = fu.result()
            results[n] = txt
            done_n += 1
            with lock:
                if txt.startswith('[OCR_') or txt.startswith('[READ'):
                    _stats['fail'] += 1
                else:
                    _stats['ok'] += 1
            if done_n % 10 == 0:
                print(f"  [{tag}] {done_n}/{len(todo)} ok={_stats['ok']} fail={_stats['fail']}", flush=True)
    # 追加写（按页序，已有页不动）
    existing = {}
    if os.path.exists(outfp):
        content = open(outfp, encoding='utf-8').read()
        for m in re.finditer(r'(===== 第 \d+ 页 =====\n.*?)(?=^===== 第 |\Z)', content, re.M | re.S):
            existing[int(re.search(r'第 (\d+) 页', m.group(1)).group(1))] = m.group(1)
    existing.update({n: f"===== 第 {n} 页 =====\n{txt}\n\n" for n, txt in results.items()})
    with open(outfp, 'w', encoding='utf-8') as fo:
        for n in sorted(existing):
            fo.write(existing[n])
    print(f"[完成] {tag} ok={_stats['ok']} fail={_stats['fail']}", flush=True)


if __name__ == '__main__':
    only = sys.argv[1:] if len(sys.argv) > 1 else list(PDFS)
    for tag in only:
        process(tag, PDFS[tag])
    print(f"\n全部完成 ok={_stats['ok']} fail={_stats['fail']}")
