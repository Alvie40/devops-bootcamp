# Roadmap — 30 dias

Plano dia a dia do bootcamp. Cada dia tem um **tema principal** (infra), um bloco de **DSA** e um bloco de **linguagem** (Python até o dia 21, Go a partir do 22). Marque o checkbox ao concluir.

---

## Como funciona o dia

Bloco de ~3h30. Se o tempo apertar, corte na ordem: linguagem → tema principal → DSA (DSA é o único inegociável, por ser hábito diário).

| Bloco | Tempo | O que fazer |
|---|---|---|
| DSA | 40 min | 2 problemas do tema do dia. Resolver sem olhar solução por 20 min, depois estudar a solução e reescrever do zero. |
| Linguagem | 45 min | Exercício prático em `python/dayNN/` ou `go/dayNN/`. Código que roda, não anotação. |
| Tema principal | 1h30 | Ler + praticar no terminal. Tudo que for comando vira script/manifesto versionado. |
| Notas + commit | 25 min | `notes/dayNN/README.md` e um commit por dia. |

### Definition of Done do dia

- [ ] O entregável do dia existe e **executa** (script roda, `terraform plan` passa, pod sobe).
- [ ] `notes/dayNN/README.md` preenchido com o template abaixo.
- [ ] Commit feito no formato `dayNN: <tema> — <entregável>`.

### Template das notas

```markdown
# Day NN — <tema>

## O que aprendi
- 3 a 5 bullets, com suas palavras.

## Comandos / trechos que valem guardar
```bash
# ...
```

## Onde travei
- O que não entendi, e o que fiz para destravar.

## Para revisar depois
- [ ] ...
```

### Estrutura de pastas

```
dsa/dayNN/            problemas resolvidos
python/dayNN/         exercícios Python (d01–d21)
go/dayNN/             exercícios Go (d22–d30)
notes/dayNN/README.md notas diárias
linux/                scripts bash e cheatsheets
networking/           labs de rede
docker/               Dockerfiles e compose
aws/                  scripts CLI e boto3
terraform/            módulos e stacks
ansible/              playbooks e roles
k8s/                  manifestos e charts
ci/                   .github/workflows espelhados + notas
observability/        prometheus, grafana, loki
projects/capstone/    projeto final (d29–d30)
```

---

## Semana 1 — Fundamentos: Python, Linux e Redes (d01–d07)

### Day 01 — Setup e Python básico
- [ ] **Tema:** ambiente (venv, pip, `requirements.txt`), estrutura do repo, fluxo de commit diário. Tipos, variáveis, `if/for/while`, f-strings, `input`/`print`.
- [ ] **DSA:** Arrays & Hashing — Two Sum, Contains Duplicate.
- [ ] **Entregável:** `python/day01/basics.py`, `dsa/day01/two_sum.py`.

### Day 02 — Python: estruturas de dados
- [ ] **Tema:** `list`, `dict`, `set`, `tuple` — quando usar cada um e o custo de cada operação. List/dict comprehensions. Slicing. Mutabilidade.
- [ ] **DSA:** Hashing — Valid Anagram, Group Anagrams.
- [ ] **Entregável:** `python/day02/collections.py` com um contador de frequência de palavras a partir de um arquivo de log.

### Day 03 — Python: funções, módulos e ambiente
- [ ] **Tema:** funções, `*args`/`**kwargs`, valores default (e a armadilha do default mutável), escopo, `import`, `__name__ == "__main__"`, venv isolado por projeto.
- [ ] **DSA:** Two Pointers — Valid Palindrome, 3Sum.
- [ ] **Entregável:** `python/day03/` como pacote com dois módulos importando um do outro.

### Day 04 — Linux I: sistema de arquivos, permissões e processos
- [ ] **Tema:** FHS (`/etc`, `/var`, `/usr`, `/proc`), navegação, `chmod`/`chown` e notação octal, usuários e grupos, `sudo`. Processos: `ps`, `top`, `kill`, sinais, foreground/background. `systemctl` para serviços.
- [ ] **DSA:** Sliding Window — Best Time to Buy and Sell Stock, Longest Substring Without Repeating Characters.
- [ ] **Entregável:** `linux/day04/cheatsheet.md` + um serviço systemd simples criado à mão.

### Day 05 — Linux II: shell scripting e texto
- [ ] **Tema:** bash (variáveis, `if`, `for`, funções, exit codes, `set -euo pipefail`), pipes e redirecionamento, `grep`/`sed`/`awk`/`cut`/`sort`/`uniq`, `find`/`xargs`, cron, logs (`/var/log`, `journalctl`).
- [ ] **DSA:** Stack — Valid Parentheses, Min Stack.
- [ ] **Entregável:** `linux/day05/log_report.sh` que extrai o top 10 de IPs e status codes de um access log.

### Day 06 — Redes I: camadas, IP e DNS
- [ ] **Tema:** OSI vs TCP/IP, endereçamento IPv4, CIDR e subnetting (treine à mão), IP público vs privado, NAT. DNS: tipos de registro, resolução recursiva, TTL. TCP three-way handshake vs UDP. Portas e serviços.
- [ ] **Ferramentas:** `dig`, `nslookup`, `ping`, `traceroute`, `ss`, `curl -v`, `tcpdump`.
- [ ] **DSA:** Binary Search — Binary Search, Search in Rotated Sorted Array.
- [ ] **Entregável:** `networking/day06/subnetting.md` com 10 exercícios de CIDR resolvidos + saída comentada de um `dig` e um `traceroute`.

### Day 07 — Redes II: HTTP, TLS, proxy e SSH — **Checkpoint 1**
- [ ] **Tema:** HTTP (métodos, status codes, headers, keep-alive), HTTPS e handshake TLS, certificados. Proxy reverso e load balancing (round robin, least conn, health checks) com nginx. Firewall (`ufw`/`iptables`). SSH: par de chaves, `~/.ssh/config`, agent, port forwarding.
- [ ] **DSA:** revisão — refaça 3 problemas da semana sem consultar nada.
- [ ] **Checkpoint:** `python/day07/healthcheck.py` — CLI que recebe uma lista de URLs, mede latência, valida status e expiração do certificado TLS, e sai com exit code diferente de zero se algo falhar.

---

## Semana 2 — Containers e Cloud (d08–d14)

### Day 08 — Python: OOP e erros
- [ ] **Tema:** classes, `__init__`, métodos de instância vs estáticos, `@dataclass`, herança vs composição, exceções (`try/except/else/finally`), exceções customizadas, `logging` (níveis, formatters, handlers).
- [ ] **DSA:** Linked List — Reverse Linked List, Merge Two Sorted Lists.
- [ ] **Entregável:** `python/day08/` refatorando o healthcheck do d07 em classes com logging estruturado.

### Day 09 — Docker I: imagens e containers
- [ ] **Tema:** namespaces e cgroups (por cima), imagem vs container, `Dockerfile` (`FROM`, `RUN`, `COPY`, `WORKDIR`, `ENV`, `EXPOSE`, `CMD` vs `ENTRYPOINT`), cache de layers, `build`/`run`/`exec`/`logs`/`ps`, volumes (bind vs named), networks e resolução de nomes entre containers.
- [ ] **DSA:** Linked List — Linked List Cycle, Remove Nth Node From End.
- [ ] **Entregável:** `docker/day09/Dockerfile` empacotando o healthcheck.

### Day 10 — Docker II: builds enxutos e compose
- [ ] **Tema:** multi-stage build, imagens base (`alpine`, `slim`, `distroless`), rodar como usuário não-root, `HEALTHCHECK`, `.dockerignore`, ordem de layers para cache. `docker compose`: services, depends_on, env, volumes.
- [ ] **DSA:** Trees — Invert Binary Tree, Maximum Depth of Binary Tree.
- [ ] **Entregável:** `docker/day10/compose.yaml` subindo app + Postgres + nginx; imagem final abaixo de 100 MB.

### Day 11 — Docker III: registry e segurança
- [ ] **Tema:** registries (Docker Hub, ECR), tags e versionamento semântico, digests, `docker push/pull`, scan de vulnerabilidades com `trivy`, gestão de secrets em imagens (o que **nunca** vai no Dockerfile), limites de recurso.
- [ ] **DSA:** Trees — Validate BST, Lowest Common Ancestor of a BST.
- [ ] **Entregável:** imagem publicada em um registry + relatório do `trivy` em `docker/day11/`.

### Day 12 — AWS I: conta e IAM
- [ ] **Tema:** modelo de responsabilidade compartilhada, regiões e AZs. IAM: users, groups, roles, policies (JSON), princípio do menor privilégio, MFA, instance profile, STS/assume role. AWS CLI: perfis, `~/.aws/config`, `--dry-run`. Billing alarm (faça isso hoje).
- [ ] **DSA:** Trees — Binary Tree Level Order Traversal (BFS), Serialize/Deserialize.
- [ ] **Entregável:** `aws/day12/policies/` com uma policy de menor privilégio escrita à mão + alarme de billing ativo.

### Day 13 — AWS II: VPC e EC2
- [ ] **Tema:** VPC, subnets pública vs privada, route tables, Internet Gateway, NAT Gateway, Security Group (stateful) vs NACL (stateless). EC2: tipos de instância, AMI, key pair, user data, EBS, Elastic IP.
- [ ] **DSA:** Heap — Kth Largest Element, Merge K Sorted Lists.
- [ ] **Entregável:** VPC com subnet pública e privada + EC2 acessível por SSH, montada pelo console **e** anotada passo a passo (você vai recriar isso em Terraform no d17).

### Day 14 — AWS III: S3, RDS e boto3 — **Checkpoint 2**
- [ ] **Tema:** S3 (buckets, chaves, storage classes, versionamento, bucket policy vs IAM, block public access, lifecycle), RDS (subnet group, backup, multi-AZ). `boto3`: client vs resource, paginators, credenciais.
- [ ] **DSA:** revisão — trees e heap.
- [ ] **Checkpoint:** app do d10 rodando containerizada numa EC2, imagem vinda do ECR, com um script `aws/day14/inventory.py` (boto3) que lista instâncias, volumes e buckets em tabela.

---

## Semana 3 — IaC, CI/CD e Go (d15–d21)

### Day 15 — Terraform I: fundamentos
- [ ] **Tema:** IaC e por que declarativo, HCL, `provider`, `resource`, ciclo `init`/`plan`/`apply`/`destroy`, arquivo de state (o que é, por que é sensível), `terraform.tfstate` local, `fmt`/`validate`.
- [ ] **DSA:** Backtracking — Subsets, Combination Sum.
- [ ] **Entregável:** `terraform/day15/` criando um bucket S3 e um security group.

### Day 16 — Terraform II: variáveis e remote state
- [ ] **Tema:** `variable` (tipos, validation, sensitive), `output`, `locals`, `data` sources, `.tfvars`, interpolação, dependências implícitas vs `depends_on`, `lifecycle`. Backend remoto S3 + lock em DynamoDB.
- [ ] **DSA:** Backtracking — Permutations, Word Search.
- [ ] **Entregável:** state migrado para backend S3 com lock funcionando (teste dois `apply` simultâneos).

### Day 17 — Terraform III: módulos
- [ ] **Tema:** módulos (locais e do registry), `for_each` vs `count`, `dynamic` blocks, estrutura de projeto por ambiente (dev/prod), `tfsec`/`checkov`, `terraform import`.
- [ ] **DSA:** Graphs — Number of Islands, Clone Graph.
- [ ] **Entregável:** módulo `terraform/modules/vpc` recriando a infra que você montou à mão no d13, com `apply` limpo.

### Day 18 — Ansible I: fundamentos
- [ ] **Tema:** push vs pull, agentless sobre SSH, inventário (INI/YAML, grupos, variáveis), comandos ad-hoc, playbooks (plays, tasks, módulos), idempotência, `--check`, `--diff`, facts.
- [ ] **DSA:** Graphs — Course Schedule (ordenação topológica), Pacific Atlantic Water Flow.
- [ ] **Entregável:** `ansible/day18/` com inventário apontando para a EC2 e um playbook que instala e configura o Docker.

### Day 19 — Ansible II: roles e templates
- [ ] **Tema:** estrutura de role (`tasks`, `handlers`, `templates`, `defaults`, `vars`), Jinja2, handlers e `notify`, loops e conditionals, `ansible-vault`, `ansible-lint`.
- [ ] **DSA:** DP 1D — Climbing Stairs, House Robber.
- [ ] **Entregável:** role que faz deploy da app containerizada com nginx configurado via template, rodando duas vezes sem mudanças (idempotente).

### Day 20 — GitHub Actions I: CI
- [ ] **Tema:** workflow/job/step, eventos (`push`, `pull_request`, `schedule`, `workflow_dispatch`), runners, `actions/checkout`, `setup-python`, matrix, cache de dependências, artifacts, status checks e branch protection.
- [ ] **DSA:** DP 1D — Coin Change, Longest Increasing Subsequence.
- [ ] **Entregável:** `.github/workflows/ci.yml` rodando `ruff` + `pytest` neste repo, verde no PR.

### Day 21 — GitHub Actions II: CD — **Checkpoint 3**
- [ ] **Tema:** secrets e variables, environments com approval, OIDC para assumir role na AWS (sem chave estática), jobs dependentes (`needs`), reusable workflows, `terraform plan` comentado no PR e `apply` no merge.
- [ ] **DSA:** revisão — backtracking e graphs.
- [ ] **Checkpoint:** pipeline completo — push na `main` → build → scan → push no ECR → `terraform apply` → deploy, autenticando por OIDC.

---

## Semana 4 — Kubernetes e Observabilidade (d22–d28)

### Day 22 — Go I: fundamentos
- [ ] **Tema:** por que Go em infra (binário estático, cross-compile), `go mod`, tipos, structs, slices vs arrays, maps, ponteiros, tratamento de erro explícito, interfaces, `go build`/`test`/`fmt`/`vet`.
- [ ] **DSA:** DP 2D — Unique Paths, Longest Common Subsequence.
- [ ] **Entregável:** `go/day22/` — CLI que faz o mesmo healthcheck do d07, compilada como binário único.

### Day 23 — Go II: concorrência e HTTP
- [ ] **Tema:** goroutines, channels, `select`, `sync.WaitGroup`, `context` (timeout e cancelamento), `net/http` servidor e cliente, `encoding/json`, flags.
- [ ] **DSA:** Intervals — Merge Intervals, Insert Interval.
- [ ] **Entregável:** servidor HTTP em Go expondo `/healthz` e `/metrics` no formato Prometheus (você vai fazer scrape dele no d27).

### Day 24 — Kubernetes I: arquitetura e workloads
- [ ] **Tema:** control plane (API server, etcd, scheduler, controller manager) e nodes (kubelet, kube-proxy, container runtime). Pod, ReplicaSet, Deployment, rolling update e rollback. `kubectl` (get/describe/logs/exec/apply), cluster local com `kind`.
- [ ] **DSA:** Greedy — Jump Game, Gas Station.
- [ ] **Entregável:** `k8s/day24/` — cluster kind + Deployment da app Go com 3 réplicas.

### Day 25 — Kubernetes II: rede e configuração
- [ ] **Tema:** Service (ClusterIP, NodePort, LoadBalancer), DNS interno, Ingress e ingress controller, ConfigMap, Secret (e por que não é criptografado por padrão), namespaces, labels e selectors.
- [ ] **DSA:** Bit Manipulation — Number of 1 Bits, Counting Bits.
- [ ] **Entregável:** app exposta por Ingress com config vinda de ConfigMap e credencial de Secret.

### Day 26 — Kubernetes III: confiabilidade
- [ ] **Tema:** liveness/readiness/startup probes, `requests` vs `limits`, QoS e OOMKill, HPA, PodDisruptionBudget, RBAC (Role, RoleBinding, ServiceAccount), PV/PVC/StorageClass, StatefulSet, Helm (chart, values, release).
- [ ] **DSA:** Matrix — Rotate Image, Spiral Matrix.
- [ ] **Entregável:** app empacotada como Helm chart com probes, limits e HPA.

### Day 27 — Prometheus
- [ ] **Tema:** modelo pull, séries temporais e labels, tipos de métrica (counter, gauge, histogram, summary), exposition format, service discovery no K8s, PromQL (`rate`, `sum by`, `histogram_quantile`), recording e alerting rules, Alertmanager (routing, silences), node_exporter, kube-state-metrics.
- [ ] **DSA:** revisão — arrays/hashing e sliding window.
- [ ] **Entregável:** Prometheus no cluster raspando o `/metrics` do d23 + 3 alertas (latência, taxa de erro, pod reiniciando).

### Day 28 — Grafana e Loki — **Checkpoint 4**
- [ ] **Tema:** Grafana (datasources, dashboards, painéis, variáveis, alerting). Loki: modelo de labels e por que difere do Elasticsearch, Promtail/agent, LogQL (filtros, parsers, agregações), correlação métrica → log.
- [ ] **DSA:** revisão — DP.
- [ ] **Checkpoint:** dashboard com os quatro golden signals (latência, tráfego, erros, saturação) + painel de logs correlacionado por `trace_id`/pod.

---

## Dias 29–30 — Projeto final

### Day 29 — Capstone: construir
- [ ] Serviço em Go (ou Python) com `/healthz` e `/metrics`.
- [ ] Imagem multi-stage, scan no CI, publicada no ECR.
- [ ] Infra em Terraform modularizado, state remoto, aplicada por OIDC.
- [ ] Deploy via Helm no cluster; configuração de host via Ansible onde couber.
- [ ] Pipeline GitHub Actions ponta a ponta.
- [ ] Prometheus + Grafana + Loki com dashboard e alertas.
- [ ] **Entregável:** `projects/capstone/` com README explicando a arquitetura e um diagrama.

### Day 30 — SRE e retrospectiva
- [ ] **Tema:** SLI, SLO e error budget (defina os do seu serviço), toil, on-call, postmortem sem culpados, runbook.
- [ ] Teste de caos simples: mate um pod, derrube uma dependência, confirme que o alerta dispara e que o dashboard mostra.
- [ ] Escreva um postmortem do incidente que você provocou.
- [ ] Retrospectiva: releia as 30 notas, liste os 5 pontos mais fracos e monte o plano dos próximos 30 dias.

---

## Convenções

**Commit:** `dayNN: <tema> — <entregável>` — ex.: `day09: docker — dockerfile do healthcheck`.

**Branch:** trabalho direto na `main` nos dias de estudo; use PR nos checkpoints (d07, d14, d21, d28) para exercitar o fluxo de review e os status checks do CI.

**Custo AWS:** `terraform destroy` ao fim de todo dia que criar recurso pago. NAT Gateway, EKS e RDS cobram por hora mesmo ociosos — prefira kind local no K8s e só suba EKS no capstone, se subir. Mantenha o alarme de billing do d12 ativo.

**Segurança:** nenhuma credencial no repo. `.env` e `*.tfstate` já estão no `.gitignore` — confirme antes de cada commit com `git status`.

**Revisão espaçada:** nos dias de checkpoint, refaça sem consultar 3 problemas de DSA das semanas anteriores. É a única parte do plano que combate esquecimento.
