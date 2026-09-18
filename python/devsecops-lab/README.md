# devsecops-lab

App FastAPI mínima usada como alvo real do crash course de DevSecOps
([notes/devsecops-crash-course.md](../../notes/devsecops-crash-course.md)). Não é
produto — é só o suficiente pra ter algo pra escanear e rodar.

## Reproduzir os scans

```bash
# SAST — audita este código
semgrep scan --config auto .

# secrets — audita o histórico do repo inteiro, não só esta pasta
gitleaks detect --source ../.. --no-banner

# SCA — audita as dependências declaradas
trivy fs --scanners vuln --severity CRITICAL,HIGH .

# build + container scan — audita a imagem final (SO base + libs)
docker build -t devsecops-lab:slim -f Dockerfile .
docker build -t devsecops-lab:full -f Dockerfile.full .
docker build -t devsecops-lab:distroless -f Dockerfile.distroless .
trivy image --severity CRITICAL,HIGH devsecops-lab:slim         # 59 vulns
trivy image --severity CRITICAL,HIGH devsecops-lab:full         # 654 vulns
trivy image --severity CRITICAL,HIGH devsecops-lab:distroless   # 49 vulns

# SBOM — gera uma vez, consulta depois sem re-escanear
syft devsecops-lab:slim -o cyclonedx-json > sbom.json
python3 -c "
import json
d = json.load(open('sbom.json'))
for c in d['components']:
    if c['name'] == 'anyio': print(c['name'], c['version'])
"  # simula checar exposição a uma CVE nova em segundos, sem re-scan

# DAST — precisa da app rodando
docker run -d --name devsecops-lab-run -p 8000:8000 devsecops-lab:slim
docker run --rm -t zaproxy/zap-stable zap-baseline.py -t http://host.docker.internal:8000/
docker stop devsecops-lab-run && docker rm devsecops-lab-run
```

Três Dockerfiles pra comparar, do pior pro melhor:

- `Dockerfile.full` — `python:3.11` completo. Só existe pra comparação (654 vulns).
- `Dockerfile` — `python:3.11-slim`, o que a CI usa hoje (59 vulns).
- `Dockerfile.distroless` — multi-stage: builder em `python:3.11-slim` faz o
  `pip install --target`, runtime final é `gcr.io/distroless/python3-debian12`
  (sem shell, sem `perl`, sem `util-linux`) — 49 vulns, 2 CRITICAL residuais
  (`libsqlite3-0`/`zlib1g`, ambas sem patch upstream disponível ainda — não é que
  não corrigimos, é que ainda não existe fix). Custo: sem shell dentro do
  container, `docker exec sh` não funciona pra debug — troca debugabilidade por
  superfície de ataque menor. Testado de pé (`curl` no `/health` responde 200 com
  os headers de segurança intactos).

CI em [.github/workflows/devsecops-lab.yml](../../.github/workflows/devsecops-lab.yml):
SAST + secrets + SCA bloqueiam o merge; container scan bloqueia em CRITICAL/HIGH
(hoje aponta pro `Dockerfile` slim); SBOM é artefato publicado, não gate; DAST só
reporta. Workflow também roda em `schedule` (segunda 06:00 UTC) pra pegar patch de
segurança na mesma tag da base image sem depender de alguém tocar no código.
[.github/dependabot.yml](../../.github/dependabot.yml) mantém `requirements.txt`,
a base image do Dockerfile e as GitHub Actions do repo em dia automaticamente.

Secrets: [.pre-commit-config.yaml](../../.pre-commit-config.yaml) na raiz do repo
roda Gitleaks antes de cada commit (`pre-commit install` uma vez pra ativar).
Achado ao testar: `AKIAIOSFODNN7EXAMPLE` (a chave de exemplo oficial da doc da AWS)
está numa allowlist padrão do Gitleaks e não é pega — uma chave aleatória no mesmo
formato é pega normalmente. Bom saber antes de "testar" o hook com a chave errada.
