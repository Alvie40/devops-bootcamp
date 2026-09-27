# Gera SVG do pipeline DevSecOps para estudo, mapeado aos estagios + toolset real
W, H = 1500, 1000
cols = {1:150, 2:380, 3:610, 4:840, 5:1070, 6:1300}
CW = 210  # card/box width
stage_y, stage_h = 660, 74
stages = {
  1:("Dev IDE","local, antes do commit"),
  2:("Source","commit / pull request"),
  3:("Build","gera artefato/imagem"),
  4:("Test","app rodando"),
  5:("Release","publica no registry"),
  6:("Runtime / Prod","ambiente no ar"),
}
# tag types
TAG = {
 "block": ("#c0392b","#fdecec","BLOCK"),
 "report":("#b8860b","#fbf3e0","REPORT"),
 "trust": ("#1e7d4f","#e9f7ef","TRUST"),
 "pre":   ("#6c3fb5","#f0eafb","HOOK"),
 "obs":   ("#2b6cb0","#e8f1fb","OBS"),
}
# cards por coluna: (titulo, sub, tag)
cards = {
 1:[("pre-commit","Gitleaks + lint no commit","pre"),
    ("SAST no IDE","Semgrep / plugin","block"),
    ("Secret scan","credencial antes do push","pre")],
 2:[("SAST","Semgrep — seu codigo","block"),
    ("SCA","Trivy fs — dependencias","block"),
    ("Secret scan","Gitleaks — historico git","block")],
 3:[("Container scan","Trivy image — CVEs da base","block"),
    ("SBOM","Syft — CycloneDX","report"),
    ("Assinar imagem","cosign sign (provenance)","trust")],
 4:[("DAST","OWASP ZAP baseline","report")],
 5:[("Verificar assinatura","cosign verify no deploy","trust"),
    ("Push por digest","@sha256, nao :latest","trust")],
 6:[("Scan no registry","imagem re-escaneada","report"),
    ("Rescan agendado","cron pega CVE nova","report"),
    ("Admission / verify","so imagem assinada roda","trust"),
    ("Observabilidade","Prometheus / Grafana","obs")],
}
card_h, card_gap, card_top = 46, 10, 150
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
p=[]
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="-apple-system,Helvetica,Arial,sans-serif">')
p.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
# titulo
p.append(f'<text x="{W/2}" y="52" text-anchor="middle" font-size="30" font-weight="700" fill="#0b2a4a">DevSecOps no pipeline CI/CD — controle por estagio</text>')
p.append(f'<text x="{W/2}" y="82" text-anchor="middle" font-size="15" fill="#5a6672">Onde cada verificacao roda, com o toolset real — e o que o video nao mostra: assinatura de imagem e runtime</text>')
# shift-left arrow
p.append(f'<line x1="620" y1="118" x2="150" y2="118" stroke="#6c3fb5" stroke-width="3" marker-end="url(#pur)"/>')
p.append(f'<text x="385" y="110" text-anchor="middle" font-size="13" font-weight="700" fill="#6c3fb5">SHIFT LEFT — detectar o mais cedo possivel</text>')
# defs
p.append('<defs>')
p.append('<marker id="arw" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#0b2a4a"/></marker>')
p.append('<marker id="pur" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#6c3fb5"/></marker>')
p.append('<marker id="gry" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#9aa7b4"/></marker>')
p.append('</defs>')
# cards + connectors
for c, cx in cols.items():
    x = cx - CW/2
    lst = cards[c]
    for i,(t,s,tag) in enumerate(lst):
        y = card_top + i*(card_h+card_gap)
        stroke,fill,label = TAG[tag]
        p.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{card_h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        p.append(f'<text x="{x+12}" y="{y+20}" font-size="14" font-weight="700" fill="#0b2a4a">{esc(t)}</text>')
        p.append(f'<text x="{x+12}" y="{y+37}" font-size="10.5" fill="#5a6672">{esc(s)}</text>')
        p.append(f'<rect x="{x+CW-56}" y="{y+7}" width="48" height="15" rx="4" fill="{stroke}"/>')
        p.append(f'<text x="{x+CW-32}" y="{y+18}" text-anchor="middle" font-size="8.5" font-weight="700" fill="#ffffff">{label}</text>')
    # connector dashed from y=430 down to stage box top
    p.append(f'<line x1="{cx}" y1="428" x2="{cx}" y2="{stage_y-2}" stroke="#c8d4e0" stroke-width="1.4" stroke-dasharray="4 4"/>')
# stage boxes + flow arrows
prev=None
for c, cx in cols.items():
    x=cx-CW/2
    name,sub=stages[c]
    p.append(f'<rect x="{x}" y="{stage_y}" width="{CW}" height="{stage_h}" rx="9" fill="#0b2a4a"/>')
    p.append(f'<text x="{cx}" y="{stage_y+30}" text-anchor="middle" font-size="16" font-weight="700" fill="#ffffff">{esc(name)}</text>')
    p.append(f'<text x="{cx}" y="{stage_y+52}" text-anchor="middle" font-size="10.5" fill="#b9c7d6">{esc(sub)}</text>')
    if prev is not None:
        p.append(f'<line x1="{prev+CW/2}" y1="{stage_y+stage_h/2}" x2="{cx-CW/2-3}" y2="{stage_y+stage_h/2}" stroke="#0b2a4a" stroke-width="2.4" marker-end="url(#arw)"/>')
    prev=cx
# baseline "CI/CD Pipeline"
p.append(f'<text x="{W/2}" y="{stage_y+stage_h+42}" text-anchor="middle" font-size="20" font-weight="700" fill="#0b2a4a" letter-spacing="2">CI / CD  PIPELINE</text>')
# legenda
ly = 812
p.append(f'<text x="40" y="{ly}" font-size="13" font-weight="700" fill="#0b2a4a">Legenda dos gates</text>')
leg=[("#c0392b","BLOCK","barra o merge/deploy (codigo, deps, secrets, CRITICAL c/ fix)"),
     ("#b8860b","REPORT","so reporta ate haver triagem (DAST, SBOM, scan de runtime)"),
     ("#1e7d4f","TRUST","cadeia de confianca — o que o video nao cobre"),
     ("#6c3fb5","HOOK","roda local, antes de existir commit"),
     ("#2b6cb0","OBS","observabilidade em producao")]
for i,(col,lab,desc) in enumerate(leg):
    yy=ly+24+i*26
    p.append(f'<rect x="40" y="{yy-12}" width="46" height="16" rx="4" fill="{col}"/>')
    p.append(f'<text x="63" y="{yy}" text-anchor="middle" font-size="8.5" font-weight="700" fill="#fff">{lab}</text>')
    p.append(f'<text x="98" y="{yy}" font-size="12" fill="#33404d">{esc(desc)}</text>')
# painel de insights (direita)
bx=760
p.append(f'<rect x="{bx}" y="800" width="700" height="168" rx="10" fill="#f4f7fa" stroke="#c8d4e0"/>')
p.append(f'<text x="{bx+20}" y="828" font-size="13" font-weight="700" fill="#0b2a4a">3 pontos que a banca vai cobrar</text>')
notes=[
 "Checagens estaticas (SAST/SCA/secrets) rodam em 3 estagios: IDE + Source + Build — nao uma vez so.",
 "Scan diz 'a imagem esta limpa'. Assinatura (cosign) diz 'e a mesma que eu construi' — sao coisas diferentes.",
 "Tag e movel e pode ser reescrita; digest @sha256 nao. Deploy por digest, nunca :latest.",
 "SBOM: exigencia do FDA para software de dispositivo medico desde 2023 — nao so boa pratica.",
 "Distroless nem sempre ganha: medi 49 CVEs (2 CRITICAL) vs slim endurecido 44 (0). Medir > supor.",
]
for i,n in enumerate(notes):
    p.append(f'<text x="{bx+20}" y="{852+i*22}" font-size="11.5" fill="#33404d">• {esc(n)}</text>')
p.append('</svg>')
open("/private/tmp/claude-501/-Users-alvie-Jobs/0497e862-cbcb-4b0f-a602-ab50c296169b/scratchpad/diag.svg","w").write("\n".join(p))
print("svg ok")
