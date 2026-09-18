# DevSecOps — relatório de scans e mitigação

Estado consolidado de tudo que foi escaneado no crash course
([devsecops-crash-course.md](devsecops-crash-course.md) tem o passo a passo de como
rodar cada ferramenta; [devsecops-interview.md](devsecops-interview.md) tem a régua
C→B e as respostas de entrevista). Este arquivo é o inventário de achados + o que já
foi corrigido de verdade + o que ainda fica em aberto e por quê.

Gerado/reverificado em **2026-09-18**.

---

## 1. Secrets (Gitleaks)

| Alvo | Resultado |
|---|---|
| `devops-bootcamp` (repo real, histórico completo) | **0 leaks** |
| Demo em repo git descartável (`gitleaks-history-demo`) | 1 leak provocado de propósito — confirmou que o histórico continua exposto mesmo depois de um commit "corrigindo" o arquivo |

**Ação de mitigação:** nenhuma no repo real (nada vazado). Playbook validado pra
quando acontecer de verdade: **rotacionar a credencial primeiro** (a chave antiga é
tratada como comprometida pra sempre, independente do repo); reescrever histórico
(`git filter-repo`) é faxina posterior, não a correção.

---

## 2. SAST (Semgrep)

| Alvo | Antes | Depois |
|---|---|---|
| `devops-bootcamp` (repo real) | 0 findings | — (nada pra corrigir) |
| `vuln_demo.py` (demo, `~/devsecops-practice/`) | 3 findings (ruleset `auto`) | **4 findings** com regra custom `os-system-injection.yaml` somada |

**Achado:** `auto` não cobria `os.system("..." + var)` (command injection), só
`subprocess.call(..., shell=True)`. Fechado escrevendo uma regra Semgrep própria.

**Ação de mitigação (como corrigir os 4 bugs do arquivo de demo, se fosse código
real):**

| Bug | Linha | Correção |
|---|---|---|
| `os.system("tar ... " + filename)` | 7 | `subprocess.run(["tar", "-czf", "backup.tar.gz", filename], shell=False)` — lista de argumentos, nunca concatenação de string |
| `subprocess.call(..., shell=True)` | 11 | mesma correção — `shell=False` + lista |
| `hashlib.md5(password...)` | 15 | trocar por `hashlib.scrypt` ou, melhor, `bcrypt`/`argon2-cffi` com salt |
| `API_KEY = "sk_live_..."` hardcoded | 18 | remover do código, ler de variável de ambiente/secrets manager; se fosse uma chave real vazada, rotacionar na Stripe |

Não aplicado no arquivo de demo em si (ele existe só pra ensinar o antes/depois) —
os padrões acima são o que se aplica ao código real daqui pra frente.

---

## 3. SCA — dependency scanning (Trivy fs)

| Alvo | Antes | Depois |
|---|---|---|
| `requirements.txt` demo (`~/devsecops-practice/`) | **20 CVEs** (3 CRITICAL, 7 HIGH, 10 MEDIUM) | **0** |

**Antes:**
```
requests==2.6.0
pyyaml==5.1
urllib3==1.24.1
```

**Depois (mitigação aplicada e reverificada):**
```
requests==2.33.0
pyyaml==6.0.2
urllib3==2.7.0
```

**Achado no processo:** a primeira tentativa de correção usou `>=` (range) em vez de
versão fixa — o Trivy **não escaneia range**, só versão pinada (`Number of
language-specific files num=0`, ele nem tentou). Lição de mitigação real: pra SCA
funcionar em CI, o manifesto tem que estar **pinado/lockado** (`==`, ou
`pip-compile`/`poetry.lock`), não com range solto — senão a ferramenta de segurança
fica cega.

---

## 4. Container scan (Trivy image) — `python/devsecops-lab/`

| Imagem | Total CRITICAL+HIGH |
|---|---|
| `Dockerfile.full` (`python:3.11` completo) | **654** (56 CRITICAL, 598 HIGH) |
| `Dockerfile` original (`python:3.11-slim`) | 62 (3 CRITICAL, 59 HIGH) |
| `Dockerfile` **depois do fix de dependência** (`fastapi>=0.115` → `starlette 1.6.0`) | **59** (3 CRITICAL, 56 HIGH) |

**Mitigação aplicada e reverificada:**
1. Trocar a base image completa por `-slim` → **654 → 62** (queda de 90,5%). Maior
   ganho isolado: quase tudo que sai é SO (Debian completo trazendo `util-linux`,
   `wget`, etc.).
2. `requirements.txt`: `fastapi==0.104.0` (que travava em `starlette 0.27.0`, 3 CVE
   HIGH) → `fastapi>=0.115` (resolveu pra `starlette 1.6.0`) → **62 → 59**.

**Tentativa que NÃO ajudou (documentado porque é a lição mais importante desta
seção):** tentei fechar as 2 CVEs restantes do Python (`jaraco.context`, `wheel`)
rodando `pip install --upgrade pip setuptools wheel` antes de instalar as
dependências. Resultado: **mesmo total (59)** — a atualização trocou
`jaraco.context`/`wheel` por **outras duas** (`setuptools CVE-2025-47273`, `msgpack
GHSA-6v7p-g79w-8964`, ambas vendorizadas dentro do próprio `pip`). Zero ganho líquido,
mais complexidade no Dockerfile e um warning novo de rodar pip como root. Revertido.
**Conclusão prática:** patch automático de tooling de packaging pode trocar um CVE
por outro sem eu perceber — sempre reverificar com o scanner depois de "corrigir",
nunca assumir que upgrade == menos risco.

**Residual aceito, e por quê:**
- **3 CRITICAL em `perl-base`** (regex/path traversal do Perl que vem com o Debian
  slim) — a app não usa Perl; é superfície de ataque morta, não exploitável neste
  contexto, mas some só quando a Debian empacotar o patch upstream e a gente
  reconstruir a imagem.
- **2 HIGH em `jaraco.context`/`wheel`** — packaging tooling da própria base image
  Python, fora do alcance do `requirements.txt`.
- Próximo passo se quiser ir além (não feito ainda): multi-stage build copiando só o
  venv pra uma imagem `distroless`/`python:3.11-slim` sem `perl`/`util-linux`, ou
  rebuild agendado (cron semanal) pra pegar patch de segurança da base image sem
  esperar um push de código.

---

## 5. SBOM (Syft)

| Alvo | Componentes |
|---|---|
| `devops-bootcamp` (repo real) | 40 (inclui GitHub Actions do CI, não só libs) |
| `~/devsecops-practice/` (demo) | 4 no CycloneDX — 3 `library` (`pyyaml`, `requests`, `urllib3`) + 1 `file` (o próprio `requirements.txt`, listado por rastreabilidade) |

**Ação de mitigação:** nenhuma — SBOM não é gate, é inventário. O valor prático é:
quando sair uma CVE nova, consultar os SBOMs já publicados em vez de re-escanear tudo.

---

## 6. DAST (OWASP ZAP baseline) — `python/devsecops-lab/`

| Rodada | PASS | WARN | FAIL |
|---|---|---|---|
| Antes (sem headers de segurança) | 64 | 3 | 0 |
| **Depois** (middleware de headers adicionado) | 66 | **1** | 0 |

**Mitigação aplicada e reverificada** — middleware em
[app.py](../python/devsecops-lab/app.py):

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response
```

Resolveu `X-Content-Type-Options Header Missing` e `Cross-Origin-Resource-Policy
Header Missing`.

**Residual aceito:** o WARN que sobrou (`Non-Storable Content`) é o **efeito
colateral esperado** do `Cache-Control: no-store` que acabei de adicionar — antes o
ZAP reclamava que o conteúdo era cacheable sem necessidade, agora reclama que não é
cacheable. Pra um endpoint de status JSON, "não cacheável" é a postura correta —
fica documentado como decisão consciente, não como bug pendente.

---

## Resumo executivo

| Categoria | Achados antes | Achados depois | Ação |
|---|---|---|---|
| Secrets | 0 (real) / 1 (demo provocada) | 0 | nenhuma — playbook validado |
| SAST | 3/4 (auto vs auto+custom) | — | regra custom escrita; padrões de fix documentados |
| SCA | 20 CVEs | **0** | versões pinadas e corrigidas, reverificado |
| Container | 654 (full) → 62 (slim) | **59** | slim + `fastapi` atualizado; 5 residuais aceitos (SO/base image, fora do app) |
| SBOM | — | 4 componentes | inventário, sem gate |
| DAST | 3 WARN | **1 WARN** | headers de segurança adicionados; 1 residual é efeito colateral esperado |

**O que ainda fica pendente de verdade** (não é "não fiz", é "decisão explícita de
não fazer agora"): multi-stage/distroless pros 5 CVEs residuais do container, e
nunca vivi uma rotação de credencial real após um leak (só simulei). Ambos citados
na régua C→B do `devsecops-interview.md`.
