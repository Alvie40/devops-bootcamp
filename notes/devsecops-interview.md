# DevSecOps — interview sheet

Respondido por escrito depois de rodar cada ferramenta de verdade contra
`python/devsecops-lab/` (ver [devsecops-crash-course.md](devsecops-crash-course.md)).
Regra do repo: só entra aqui o que eu consigo responder sem roteiro.

**SAST vs DAST vs SCA — uma frase cada?**
SAST lê o código-fonte que eu escrevi, sem executar nada. DAST ataca a aplicação já
rodando, de fora, como um atacante real. SCA audita as bibliotecas de terceiros que
o projeto importa, não o código próprio.

**Por que SAST não é oráculo?**
Cobertura depende do ruleset carregado. Vivi isso: no mesmo arquivo, Semgrep pegou
`subprocess.call(..., shell=True)` como command injection mas não pegou
`os.system("tar ... " + filename)`, que é a mesma classe de bug com sintaxe
diferente. Por isso SAST é uma camada — nunca a única — e não substitui code review.

*Fechei o gap na prática, não só observei*: escrevi uma regra Semgrep própria
(`os-system-injection.yaml`, pattern `os.system("..." + $VAR)`) e rodei
`semgrep scan --config auto --config os-system-injection.yaml vuln_demo.py` — foi de
3 pra **4 findings**, com a regra custom pegando exatamente a linha que faltava. O
argumento de entrevista fica mais forte assim: quando um ruleset genérico não cobre
um padrão específico do seu codebase, a resposta é escrever a regra (leva minutos),
não aceitar o gap.

**O que é SBOM e pra que serve quando sai uma CVE nova (ex.: Log4Shell)?**
É o inventário de tudo que compõe o artefato — não só libs de linguagem, também
imagens base e até GitHub Actions usadas no CI (foi o que o Syft achou no
`devops-bootcamp`: 40 componentes, incluindo `actions/checkout`). Quando sai uma CVE
nova, em vez de escanear todo o parque de novo, eu consulto os SBOMs já publicados e
sei em minutos quais artefatos usam o componente afetado.

*Pratiquei o consumo, não só a geração*: simulei uma CVE hipotética em
`anyio < 4.16.0` e, em vez de rodar o Trivy de novo, li o `sbom.json` já gerado e
achei `anyio 4.15.1` (exposto) em milissegundos. Numa lista real de dezenas de
serviços é a diferença entre responder em 1 minuto ou levar a tarde toda
re-escaneando tudo.

**Container scan: por que escanear a imagem além do código?**
Porque o código nunca vê o SO base nem os pacotes que vêm com ele — e é ali que
mora a maior parte do risco. Medido de verdade: `python:3.11` completo deu 654
vulnerabilidades CRITICAL/HIGH; trocando só a base pra `python:3.11-slim`, sem tocar
em uma linha de app, caiu pra 59 (queda de 91%). Blast radius da base image é maior
que o do meu código.

**Foi além do slim: quando vale ir pra distroless, e qual o custo?**
Fiz um multi-stage build (`python:3.11-slim` só pra instalar dependências,
`gcr.io/distroless/python3-debian12` como runtime final) e caiu de 59 pra 49 — o
`perl-base` e o `util-linux` (que geravam os 3 CRITICAL do slim) somem inteiros,
porque distroless nunca instala pacotes que a app não precisa em runtime, incluindo
shell. Testei que a app continua funcionando (`curl /health` → 200, headers
intactos) antes de confiar no número. **O custo real:** sem shell, `docker exec sh`
não funciona — se algo quebrar em produção, não dá pra entrar no container pra
investigar do jeito tradicional; depende de logs bem feitos e observability
externa. É uma troca deliberada (superfície de ataque menor por debugabilidade
menor), não um "sempre use distroless".

**O que é DAST pega que SAST não pega (e vice-versa)?**
DAST viu o que rodou de verdade contra a app: `X-Content-Type-Options` ausente,
`Cross-Origin-Resource-Policy` ausente, conteúdo cacheable sem necessidade — tudo
config de runtime/header, invisível lendo o `app.py`. Por outro lado DAST não teria
achado o command injection do `vuln_demo.py`, porque nunca ia exercitar aquele
caminho de código sem eu mandar o input certo — isso é papel do SAST.

**O que é SSDLC?**
Não é ferramenta, é processo: segurança embutida em cada fase do desenvolvimento
(design → código → build → deploy → operação), não só um scan no final antes do
release.

**Onde secrets scanning entra no fluxo, e por que remover a chave do arquivo não
resolve?**
Entra em dois pontos: pre-commit hook (pega antes de existir commit) e CI (rede de
segurança se o hook não rodou local). Gitleaks escaneia o **histórico do git**, não
só o working tree — apaguei a linha do arquivo, a chave continua existindo no commit
antigo. A remediação certa é rotacionar a credencial; reescrever histórico
(`git filter-repo`) só se for realmente grave, sabendo que quebra clone existente.

*Demo que provou isso na prática (repo git descartável, 17/09/2026):*

```bash
git init && git config user.email demo@local && git config user.name demo

echo 'API_KEY = "sk_live_[REDACTED-fake-key-used-for-this-demo]"' > config.py
git add config.py && git commit -m "add config with api key"
SECRET_COMMIT=$(git rev-parse HEAD)

echo 'API_KEY = "read from env, not hardcoded"' > config.py
git add config.py && git commit -m "fix: remove hardcoded key"

cat config.py                      # arquivo HOJE: sem chave
gitleaks detect --source . -v      # mesmo assim acha o leak, apontando o commit antigo
git show "$SECRET_COMMIT":config.py  # prova: o commit antigo ainda devolve a chave inteira
```

Resultado real: o `cat config.py` de hoje não mostra chave nenhuma, mas o Gitleaks
achou o leak apontando `Commit: 35f168a...` (o commit de 2 atrás) — porque ele varre
commit por commit, não o snapshot atual. E `git show 35f168a:config.py` devolveu a
chave inteira de volta, provando que ela nunca saiu do repositório, só saiu da
versão mais recente do arquivo. Qualquer pessoa com o clone recupera em segundos
(`git log -p`, ou rodando o mesmo Gitleaks). Por isso a única correção real é
rotacionar a credencial — a chave vazada fica comprometida pra sempre, independente
do que acontecer no repo depois; reescrever histórico é faxina posterior, não
remediação.

**Instalei o hook de verdade — e bati numa allowlist padrão sem esperar.**
[.pre-commit-config.yaml](../.pre-commit-config.yaml) roda Gitleaks antes de cada
commit. Testei com `AWS_KEY = "AKIAIOSFODNN7EXAMPLE"` (achando que ia bloquear) e
**passou** — só descobri o porquê investigando: essa string exata é o placeholder
oficial que a própria documentação da AWS usa em todo tutorial, e o Gitleaks tem
ela numa allowlist padrão pra não gerar ruído com exemplo de doc. Repeti com
uma chave `AKIA…` gerada aleatoriamente (não reproduzida aqui — colar o valor
literal numa doc é o mesmo erro que o hook existe pra pegar) e o hook bloqueou de verdade
(`exit code 1`, commit não foi criado). Lição de entrevista: toda ferramenta de
scanning tem allowlist padrão pra reduzir falso positivo — bom saber que existe
antes de testar um hook e concluir errado que ele não funciona.

**Blocking vs non-blocking security gate — como decidir?**
No pipeline que montei: SAST, secrets e SCA (CRITICAL/HIGH) bloqueiam o merge —
são coisas corrigíveis na hora, num projeto sob meu controle. Container scan bloqueia
em CRITICAL/HIGH pela mesma lógica (é a etapa que capturou o 649→57). SBOM nunca
bloqueia — é artefato, não gate. DAST só reporta — um baseline scan pega coisas
(header ausente) que às vezes exigem decisão de arquitetura, não fix de uma linha sob
pressão de CI; virar gate exigiria triagem prévia pra não travar todo merge por algo
que ainda não foi avaliado.

## Régua C→B aplicada (atualizado 18/09/2026)

- **SAST (Semgrep):** B, todos os 8 critérios — expliquei sem roteiro,
  instalei/configurei (incluindo regra custom em YAML), usei em projeto real,
  provoquei falha (demo), diagnostiquei o gap de cobertura, **recuperei** (escrevi
  `os-system-injection.yaml` e fechei o gap, 3→4 findings), expliquei tradeoffs,
  respondo pergunta de entrevista. Falta só viver isso num incidente de produção
  real — até aqui é tudo demo própria, honesto deixar isso claro na entrevista.
- **SCA (Trivy fs):** **B+** — além dos 8 critérios, mitiguei de verdade (versões
  pinadas corrigidas, 20→0 CVEs reverificado) e bati numa armadilha real: a primeira
  tentativa usou `>=` e o Trivy nem escaneou; só `==` fixado funciona. Relatório
  completo em [devsecops-scan-report.md](devsecops-scan-report.md).
- **Container scan (Trivy image):** **B+** — build, scan, comparação com número
  real (654→59 trocando pra `-slim` + atualizando `fastapi`/`starlette`; 59→49 com
  multi-stage `distroless`), um caso documentado de mitigação que **não** ajudou
  (`pip install --upgrade pip setuptools wheel` trocou 2 CVEs por outras 2 —
  revertido) e um caso que ajudou de verdade removendo a categoria inteira do
  problema (distroless nunca instala `perl`/`util-linux`, em vez de tentar
  atualizá-los). Os 2 CRITICAL residuais (`libsqlite3-0`, `zlib1g`) não têm fix
  upstream disponível ainda — confirmado no próprio output do Trivy
  (`Fixed Version: None`), não é gap de esforço.
- **SBOM (Syft):** **B** — instalei, gerei, expliquei o "porquê" com exemplo
  concreto (Log4Shell), e consumi o SBOM de verdade: simulei uma CVE hipotética em
  `anyio < 4.16.0` e confirmei exposição consultando o `sbom.json` já gerado
  (`anyio 4.15.1`) em vez de re-escanear a imagem.
- **Secrets (Gitleaks):** **B** — pre-commit hook instalado e testado nos dois
  sentidos: bloqueou de verdade uma chave AWS aleatória, e **deixou passar**
  `AKIAIOSFODNN7EXAMPLE` — achado real de que essa chave específica está numa
  allowlist padrão do Gitleaks (é o placeholder oficial da doc da AWS). Falta só o
  critério 6 pleno — rotação de credencial após um leak real de produção, não
  simulado.
- **DAST (ZAP):** **B** — rodei, expliquei a diferença de SAST, e mitiguei 2 dos 3
  achados de verdade (middleware de security headers, 3 WARN → 1 WARN); o residual
  é efeito colateral esperado do próprio fix (`Cache-Control: no-store` vira
  "non-storable" no scan), documentado como decisão consciente. Scan autenticado
  fica de fora por decisão de escopo — exigiria adicionar autenticação à app só
  pra testar a ferramenta.
