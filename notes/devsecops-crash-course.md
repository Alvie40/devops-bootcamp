# DevSecOps tools — crash course (2 dias, hands-on)

Motivação: gap recorrente nas vagas Staff/Senior DevSecOps (ex.: Analog Devices,
candidatura 19/08, call com Casey Galvin 22/09) — SAST/DAST/SCA/SBOM/SSDLC eram só
sigla. Objetivo aqui não é decorar termo pra sobreviver a uma call de 15 min, é sair
sabendo instalar, rodar, ler o output e provocar falha em cada ferramenta — a régua
C→B do `ROADMAP-FTE.md` aplicada a este domínio. Não substitui o FTE roadmap nem a
trilha C++ (que continua prioridade — ver memória `cpp-hft-track`); é um desvio curto
e dirigido a uma oportunidade real no funil.

Ferramentas escolhidas: as que dá pra rodar sozinho, de graça, na hora — sem esperar
acesso a conta AWS/GCP nem a um SOC2 de verdade.

---

## Dia 1 — Shift-left (código e dependências) — ✅ feito em 2026-09-17

Tudo instalado via `brew install semgrep gitleaks trivy syft`.

### 1. Secrets scanning — Gitleaks

```bash
gitleaks detect --source . --no-banner
```

Rodado contra todo o histórico do `devops-bootcamp` (12 commits) → **0 leaks**.
Ponto de entrevista: gitleaks lê o **histórico do git**, não só o working tree — por
isso "remover a chave do arquivo" não resolve, ela continua no commit antigo; a
resposta certa é rotacionar a credencial e, se for grave, reescrever histórico
(`git filter-repo`) sabendo que isso quebra clones existentes.

### 2. SAST — Semgrep

```bash
semgrep scan --config auto .
```

Rodado contra o repo real (C, C++, Python) → **0 findings** (código limpo). Pra ver
a ferramenta pegar algo de verdade, criei um arquivo só de demonstração
(`vuln_demo.py`, fora do repo, no scratchpad) com três problemas clássicos e rodei de
novo:

```python
subprocess.call("tar -czf backup.tar.gz " + filename, shell=True)   # command injection
hashlib.md5(password.encode()).hexdigest()                          # hash fraco pra senha
API_KEY = "sk_live_[REDACTED-fake-key-used-for-this-demo]"              # secret hardcoded
```

Semgrep achou os **3** (`subprocess-shell-true`, `md5-used-as-password`,
`detected-stripe-api-key`) — mas **não** flagou o `os.system("tar ... " + filename)`
equivalente logo acima no mesmo arquivo, que também é command injection. Achado
importante pra entrevista: **SAST não é oráculo** — cobertura depende do ruleset, e um
padrão sintaticamente diferente do mesmo bug pode escapar. Por isso SAST é *uma*
camada, nunca a única (complementa code review humano e testes).

**Praticado de novo à mão (não só observado) em `~/devsecops-practice/`,
reproduzindo o mesmo gap** — e fechando ele com uma regra Semgrep própria:

```yaml
# os-system-injection.yaml
rules:
  - id: os-system-string-concat
    languages: [python]
    severity: ERROR
    message: >
      os.system() com concatenação de string é command injection: se
      'filename' vier de input externo, um atacante controla o shell.
      Use subprocess.run([...], shell=False) com argumentos em lista.
    patterns:
      - pattern: os.system("..." + $VAR)
```

```bash
semgrep scan --config auto --config os-system-injection.yaml vuln_demo.py
# Ran 291 rules on 1 file: 4 findings.
```

Passou de 3 pra **4 findings** — a regra custom (`os-system-string-concat`) casou
exatamente com a linha 7 que o ruleset `auto` deixava passar. Fecha o argumento de
entrevista: quando um SAST genérico não cobre um padrão do seu codebase, a resposta
não é "aceitar o gap", é escrever a regra — leva minutos, não precisa esperar o
Semgrep Registry adicionar suporte.

### 3. SCA (dependency scanning) — Trivy fs

```bash
trivy fs --scanners vuln .
```

Contra um `requirements.txt` de demonstração com versões antigas de propósito
(`requests==2.6.0`, `pyyaml==5.1`, `urllib3==1.24.1`) → **20 CVEs reais** (3 CRITICAL,
7 HIGH, 10 MEDIUM), incluindo `CVE-2019-20477` (PyYAML, execução de comando via
`FullLoader`) e `CVE-2018-18074` (requests, header `Authorization` sobrevive a
redirect HTTPS→HTTP). Diferença SAST vs SCA pra entrevista: SAST audita **código que
você escreveu**; SCA audita **código de terceiros que você importa** — é a categoria
onde Dependabot/`pip-audit`/`npm audit` também vivem, e é o motivo de existir SBOM
(saber rápido se uma CVE nova te afeta sem escanear tudo de novo).

### 4. SBOM — Syft

```bash
syft dir:. -o cyclonedx-json
```

Gerou SBOM do repo (**40 componentes** em CycloneDX) — inclusive GitHub Actions
usadas em workflows (`actions/checkout`, `actions/setup-python`), não só pacotes de
linguagem. É o ponto que estava mais abstrato antes de rodar: SBOM não é "lista de
libs Python", é inventário de **tudo que compõe o artefato**, incluindo CI actions e
imagens base — por isso interessa pra supply chain, não só pra dependência de app.

**Pendência do dia 1:** o comando `syft` reclamou de "no explicit name and version
provided for directory source" — não travou, mas é o tipo de aviso que merece nome/
versão explícitos (`syft dir:. --source-name devops-bootcamp --source-version
$(git rev-parse --short HEAD)`) num pipeline de CI real, pra o SBOM carregar versão
rastreável em vez de hash de diretório.

---

## Dia 2 — Container, runtime e pipeline — ✅ feito em 2026-09-17

Alvo real criado em [python/devsecops-lab/](../python/devsecops-lab/) (FastAPI
mínima, deliberadamente simples — é só o suficiente pra ter algo pra escanear).

### 5. Container scanning — Trivy image

```bash
docker build -t devsecops-lab:full -f Dockerfile.full .   # python:3.11 completo
trivy image --severity CRITICAL,HIGH devsecops-lab:full   # 649 vulnerabilidades
docker build -t devsecops-lab:slim -f Dockerfile .         # python:3.11-slim
trivy image --severity CRITICAL,HIGH devsecops-lab:slim   # 57 vulnerabilidades
```

**649 → 57** (queda de 91%) só trocando a base image, sem tocar em uma linha de
app. Quase toda a diferença é SO (Debian completo trazendo `util-linux`, `wget` etc.
com dezenas de CVE cada) — a app em si (`fastapi`/`starlette`/`wheel`) contribuiu só
5 HIGH. Fixa de vez a resposta pra "por que escanear a imagem além do código?": o
código nunca vê o que vem dentro da base image, e é ali que mora a maior parte do
risco.

### 6. DAST — OWASP ZAP (baseline scan)

```bash
docker run -d --name devsecops-lab-run -p 8000:8000 devsecops-lab:slim
docker run --rm -t zaproxy/zap-stable zap-baseline.py -t http://host.docker.internal:8000/
```

Resultado real: **64 PASS, 3 WARN, 0 FAIL** — `X-Content-Type-Options` ausente,
conteúdo cacheable sem necessidade, `Cross-Origin-Resource-Policy` ausente. Nenhum
desses aparece lendo o `app.py` (são 12 linhas, sem bug de lógica) — é exatamente a
diferença de DAST: ataca a aplicação **de fora, já rodando**, e enxerga config de
runtime que SAST nunca veria. Ao mesmo tempo, o ZAP baseline nunca acharia o command
injection do `vuln_demo.py` do dia 1 — não ia adivinhar o input certo pra exercitar
aquele caminho.

### 7. Pipeline — GitHub Actions

Workflow em [.github/workflows/devsecops-lab.yml](../.github/workflows/devsecops-lab.yml),
escopado por `paths:` a `python/devsecops-lab/**`:

`sast (Semgrep) + secrets (Gitleaks) + sca (Trivy fs)` em paralelo, bloqueantes →
`container-scan (build + Trivy image)`, bloqueante em CRITICAL/HIGH → `sbom (Syft,
CycloneDX)`, artefato publicado, nunca bloqueia → `dast (ZAP baseline)`, roda em
paralelo ao SBOM, só reporta.

Política de blocking vs non-blocking (a decisão que a entrevista costuma sondar):
código e dependências próprias bloqueiam sempre porque são corrigíveis na hora, sob
controle direto; DAST só reporta porque um finding de baseline scan pode exigir
decisão de arquitetura, não fix de uma linha — virar gate sem triagem prévia trava
todo merge por algo que ainda não foi avaliado.

### 8. Interview day

Perguntas + régua C→B por ferramenta em [notes/devsecops-interview.md](devsecops-interview.md).
Resultado: SAST, SCA e container scan já em **B** (passaram pelos 8 critérios com
demo própria); SBOM e DAST em **C+**; secrets em **C** (nunca vivi um leak real,
falta praticar rotação/recuperação de credencial de verdade).

---

## Não estudar agora (fora do escopo deste crash course)

Certificação (CISSP/CSSLP/CKS) · SIEM/SOAR · compliance formal (ISO 27001/SOC 2 —
ficam como "sei o que é", não "operei") · threat modeling formal (STRIDE) — só entra
se aparecer de novo em mais de uma vaga forte no funil do job-bot.
