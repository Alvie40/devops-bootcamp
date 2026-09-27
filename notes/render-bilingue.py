import re, sys, html

src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding='utf-8').read().split('\n')

def inline(s):
    s = html.escape(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    return s


def join(parts):
    s = ''
    for p in parts:
        p = p.strip()
        if not s:
            s = p
        elif s.endswith('-') and not s.endswith('--') and p[:1].isalpha():
            s += p          # hifen de quebra de linha: une sem espaco
        else:
            s += ' ' + p
    return s

out, i, prev = [], 0, ''
while i < len(lines):
    ln = lines[i]
    if not ln.strip():
        i += 1; prev = ''; continue
    if ln.startswith('# '):
        out.append(f'<h1>{inline(ln[2:])}</h1>'); prev = 'h1'; i += 1; continue
    if ln.startswith('## '):
        out.append(f'<h2>{inline(ln[3:])}</h2>'); prev = 'h2'; i += 1; continue
    if ln.startswith('### '):
        out.append(f'<h3>{inline(ln[4:])}</h3>'); prev = 'h3'; i += 1; continue
    if ln.strip() == '---':
        i += 1; prev = ''; continue
    # linha traduzida em italico: *...*
    if re.match(r'^\*[^*].*\*$', ln.strip()) and not ln.startswith('**'):
        txt = ln.strip()[1:-1]
        cls = 'h1pt' if prev == 'h1' else ('h2pt' if prev == 'h2' else 'qpt')
        out.append(f'<p class="{cls}">{inline(txt)}</p>'); prev = cls; i += 1; continue
    # pergunta EN em negrito (pode ocupar 1+ linhas ate fechar **)
    if ln.startswith('**'):
        buf = [ln]
        # so continua se houver ** em aberto (contagem impar); tag apos o ** fecha a linha
        while ' '.join(buf).count('**') % 2 == 1 and i + 1 < len(lines):
            i += 1; buf.append(lines[i])
        txt = join(buf).strip()
        out.append(f'<p class="qen">{inline(txt)}</p>'); prev = 'qen'; i += 1; continue
    # bloco de codigo cercado (```)
    if ln.lstrip().startswith('```'):
        buf = []
        i += 1
        while i < len(lines) and not lines[i].lstrip().startswith('```'):
            buf.append(lines[i]); i += 1
        i += 1  # pula o fechamento
        code = '\n'.join(buf)
        import html as _h
        out.append('<pre class="code"><code>' + _h.escape(code) + '</code></pre>')
        prev = 'code'; continue
    # diagrama SVG cru (passa direto, centralizado)
    if ln.lstrip().startswith('<svg'):
        buf = [ln]
        while '</svg>' not in buf[-1] and i + 1 < len(lines):
            i += 1; buf.append(lines[i])
        out.append('<div class="diagram">' + '\n'.join(buf) + '</div>')
        prev = 'diagram'; i += 1; continue
    # lista com marcadores
    if ln.lstrip().startswith('- '):
        items = []
        while i < len(lines) and lines[i].strip():
            cur = lines[i]
            if cur.lstrip().startswith('- '):
                items.append([cur.lstrip()[2:].strip()])
            elif items:
                items[-1].append(cur.strip())
            else:
                break
            i += 1
        lis = ''.join(f'<li>{inline(join(parts))}</li>' for parts in items)
        out.append(f'<ul>{lis}</ul>'); prev = 'ul'; continue
    # tabela markdown
    if ln.lstrip().startswith('|'):
        rows = []
        while i < len(lines) and lines[i].lstrip().startswith('|'):
            cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
            rows.append(cells); i += 1
        body_rows = [r for r in rows[1:] if not all(set(c) <= set('-: ') for c in r)]
        th = ''.join(f'<th>{inline(c)}</th>' for c in rows[0])
        trs = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
                      for r in body_rows)
        out.append(f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>')
        prev = 'table'; continue
    # bloco de citacao = resposta traduzida
    if ln.startswith('>'):
        buf = []
        while i < len(lines) and lines[i].startswith('>'):
            buf.append(lines[i].lstrip('>').strip()); i += 1
        out.append(f'<p class="apt">{inline(join(buf))}</p>'); prev = 'apt'; continue
    # paragrafo normal = resposta EN (ou texto corrido)
    buf = []
    while i < len(lines) and lines[i].strip() and not lines[i].startswith(('>', '#', '**')) \
          and lines[i].strip() != '---' and not lines[i].lstrip().startswith(('- ', '|')) \
          and not re.match(r'^\*[^*].*\*$', lines[i].strip()):
        buf.append(lines[i].strip()); i += 1
    if not buf:                     # nada consumido: nunca deixar o indice parado
        out.append(f'<p class="aen">{inline(lines[i].strip())}</p>'); i += 1
    else:
        out.append(f'<p class="aen">{inline(join(buf))}</p>')
    prev = 'aen'

body = '\n'.join(out)
# agrupar cada Q&A num bloco que nao quebra no meio da pagina
body = re.sub(r'(<p class="qen">.*?)(?=<p class="qen">|<h2>|$)',
              lambda m: f'<div class="qa">{m.group(1)}</div>', body, flags=re.S)

css = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
       font-size: 10.2pt; line-height: 1.45; color: #1b1f23; margin: 0; }
h1 { font-size: 19pt; margin: 0 0 2px; color: #0b2a4a; }
.h1pt { font-size: 12.5pt; color: #5a6672; font-style: italic; margin: 0 0 14px;
        border-bottom: 2px solid #0b2a4a; padding-bottom: 10px; }
h2 { font-size: 13pt; color: #0b2a4a; margin: 22px 0 0; padding-top: 10px;
     border-top: 1px solid #c8d4e0; page-break-after: avoid; }
.h2pt { font-size: 10.5pt; color: #5a6672; font-style: italic; margin: 0 0 10px;
        page-break-after: avoid; }
ul { margin: 4px 0 10px; padding-left: 18px; }
li { margin-bottom: 3px; }
h3 { font-size: 11pt; color: #0b2a4a; margin: 14px 0 4px; page-break-after: avoid; }
.qa { page-break-inside: avoid; margin-bottom: 13px; }
.qen { font-weight: 700; color: #0b2a4a; margin: 0 0 1px; page-break-after: avoid; }
.qpt { font-style: italic; color: #6b7783; margin: 0 0 6px; font-size: 9.6pt;
       page-break-after: avoid; }
.aen { margin: 0 0 5px; }
.apt { margin: 0 0 4px; padding-left: 9px; border-left: 3px solid #b9c7d6;
       color: #46525e; font-size: 9.6pt; }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 88%;
       background: #f1f4f7; padding: 0.5px 3px; border-radius: 3px; color: #10395e; }
strong { color: inherit; }



pre.code { background: #0b2a4a; color: #e8f0f8; font-family: "SF Mono", Menlo, Consolas, monospace;
           font-size: 9.2pt; line-height: 1.5; padding: 10px 12px; border-radius: 7px;
           margin: 8px 0 12px; white-space: pre-wrap; word-break: break-word; page-break-inside: avoid; }
pre.code code { background: none; color: inherit; padding: 0; }
.diagram { margin: 14px 0 18px; text-align: center; page-break-inside: avoid; }
.diagram svg { max-width: 100%; height: auto; }
table { width: 100%; border-collapse: collapse; margin: 6px 0 14px;
        font-size: 9.1pt; page-break-inside: avoid; }
th { background: #eaf0f6; color: #0b2a4a; text-align: left; font-weight: 700;
     padding: 5px 7px; border: 1px solid #c8d4e0; }
td { padding: 5px 7px; border: 1px solid #d8e0e8; vertical-align: top; }
tbody tr:nth-child(even) { background: #f7f9fb; }

"""
open(dst, 'w', encoding='utf-8').write(
    f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
    f'<title>DevSecOps Interview Q&amp;A — 120 Questions (EN/PT-BR)</title>'
    f'<style>{css}</style></head><body>{body}</body></html>')
print("html ok")
