#!/usr/bin/env python3
"""md 精读笔记 → 学习库暗色 HTML（样式复用既有模板）"""
import re, sys, html as htmllib

STYLE_SRC = '/home/lilis/study-library/z-lib_文本版/精读笔记_透视繁荣_资产重估与流动性冲击.html'

def inline(s):
    s = htmllib.escape(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
    return s

def md2body(md):
    lines = md.split('\n')
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1; continue
        if s == '---':
            out.append('<hr>'); i += 1; continue
        if s.startswith('### '):
            out.append(f'<h3>{inline(s[4:])}</h3>'); i += 1; continue
        # markdown 表格
        if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:\-|]+\|?$', lines[i+1].strip()):
            header = [c.strip() for c in s.strip('|').split('|')]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            th = ''.join(f'<th>{inline(c)}</th>' for c in header)
            trs = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows)
            out.append(f'<div class="tblwrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue
        if s.startswith('## '):
            out.append(f'<h2>{inline(s[3:])}</h2>'); i += 1; continue
        if s.startswith('# '):
            out.append(f'<h1>{inline(s[2:])}</h1>'); i += 1; continue
        if s.startswith('> '):
            buf = [s[2:]]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('> '):
                buf.append(lines[i].strip()[2:]); i += 1
            out.append('<blockquote>' + '<br>'.join(inline(x) for x in buf) + '</blockquote>')
            continue
        if s.startswith('- ') or re.match(r'^(\d+)\.\s', s):
            ordered = bool(re.match(r'^\d+\.\s', s))
            tag = 'ol' if ordered else 'ul'
            items = []
            pat = r'^\d+\.\s' if ordered else r'^-\s'
            while i < len(lines):
                s2 = lines[i].strip()
                if not re.match(pat, s2): break
                items.append(re.sub(pat, '', s2, count=1))
                i += 1
            lis = ''.join(f'<li>{inline(x)}</li>' for x in items)
            out.append(f'<{tag}>{lis}</{tag}>')
            continue
        # 普通段落（吞并后续非结构行）
        buf = [s]; i += 1
        while i < len(lines):
            s2 = lines[i].strip()
            if not s2 or s2.startswith(('#', '> ', '- ')) or s2 == '---' or re.match(r'^\d+\.\s', s2):
                break
            buf.append(s2); i += 1
        out.append('<p>' + inline(' '.join(buf)) + '</p>')
    return '\n'.join(out)

def convert(md_path, html_path, title):
    src = open(STYLE_SRC, encoding='utf-8').read()
    style = src[:src.find('</style>') + len('</style>')]
    md = open(md_path, encoding='utf-8').read()
    body = md2body(md)
    out = f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{htmllib.escape(title)}</title>{style}<style>.tblwrap{{overflow-x:auto;-webkit-overflow-scrolling:touch}}</style></head><body><div class="wrap">{body}</div></body></html>'
    open(html_path, 'w', encoding='utf-8').write(out)
    print('✓', html_path)

if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2], sys.argv[3])
