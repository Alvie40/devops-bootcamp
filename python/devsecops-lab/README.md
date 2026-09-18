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
trivy image --severity CRITICAL,HIGH devsecops-lab:slim   # 57 vulns
trivy image --severity CRITICAL,HIGH devsecops-lab:full   # 649 vulns

# SBOM
syft dir:. -o cyclonedx-json

# DAST — precisa da app rodando
docker run -d --name devsecops-lab-run -p 8000:8000 devsecops-lab:slim
docker run --rm -t zaproxy/zap-stable zap-baseline.py -t http://host.docker.internal:8000/
docker stop devsecops-lab-run && docker rm devsecops-lab-run
```

`Dockerfile` (produção, `python:3.11-slim`) vs `Dockerfile.full` (`python:3.11`
completo, só existe pra comparação) — a diferença de 649→57 vulnerabilidades é o
argumento prático pra sempre preferir base image mínima.

CI em [.github/workflows/devsecops-lab.yml](../../.github/workflows/devsecops-lab.yml):
SAST + secrets + SCA bloqueiam o merge; container scan bloqueia em CRITICAL/HIGH;
SBOM é artefato publicado, não gate; DAST só reporta.
