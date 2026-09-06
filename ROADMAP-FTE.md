# Roadmap FTE — 8 semanas (v2)

Plano orientado a entrevista para vagas FTE nos EUA (foco Massachusetts): fechar os gaps que hoje reduzem o match para **Senior Cloud / Infrastructure / DevOps / SRE-adjacent**, transformando experiência real em respostas fortes — sem tratar o Álvaro como iniciante.

**Fontes canônicas** (o plano parte delas e nunca as contradiz):
- Currículo: `resume/alvaro-lopes-resume.md` — hoje o canônico em disco é `~/Repo/cv/2026-08_alvaro-lopes_geral_pt.md`.
- Matriz factual: `resume/alvaro-lopes-claim-matrix.md` (ainda não existe em disco — criar/localizar antes da S1; até lá, valem as regras do currículo canônico).

**Regra inegociável do currículo (16/08/2026):** Terraform, Ansible, Prometheus, Grafana e Datadog têm experiência **zero** — não entram em currículo nem cover letter até serem promovidos pela régua da seção *Claim matrix* abaixo. Não usar "SLO" para descrever a experiência da Nova (era SLA de suporte).

**Ambiente real validado** (base das respostas de entrevista — nunca inventar acima disso):
- **Satflow** → AWS Lightsail.
- **SatPsy** → Hostinger, **3-node self-managed k3s**: Traefik, Longhorn, CloudNativePG, SealedSecrets, NetworkPolicy, private registry.
- CI/CD: **Gitea Actions self-hosted** (runners, private registry, Postgres service container) + **GitHub Actions** em projetos reais.
- **Althora**: home datacenter desligado → estratégia de religamento em [ALTHORA.md](ALTHORA.md); vira o lab de Ansible/observability/incidentes a partir da S3.

Não gastar semanas com Linux básico, Docker básico ou Kubernetes introdutório — isso já é experiência real.

---

## Como funciona

### Rotina

**Seg–sex, 2–3h:** 30 min teoria → 60–90 min lab → 30–45 min interview prep. **Fim de semana:** 1 bloco maior (capstone incremental, troubleshooting, Althora, revisão, documentação). Se o dia apertar, corta na ordem: teoria → interview prep → **lab nunca**.

Toda sessão termina produzindo pelo menos um destes: código, configuração, lab, troubleshooting, documentação, arquitetura, resposta de entrevista ou melhoria real em projeto. A pergunta constante: **"isso aumenta minha chance de passar numa entrevista nas próximas semanas?"** Proibido: maratona de vídeo, curso longo sem prática, certificação por certificação, leitura desconectada.

### Daily log — `career/study-log.md`

```text
Date:
Topic:
What I built:
What broke:
How I fixed it:
Interview questions:
Skill status:
Next action:
```

O log é material de entrevista ("what broke / how I fixed it" = histórias prontas). Commit diário: `fte sN.dN: <tema> — <entregável>`.

### Weekly review (domingo, 30 min)

1. O que aprendi? 2. O que consigo **demonstrar**? 3. Qual skill mudou C→B? 4. Quais vagas apareceram? 5. Onde fui rejeitado? 6. Quais perguntas de entrevista surgiram? 7. O plano precisa mudar?

### Métricas de sucesso

Não medir horas assistidas. Medir: labs completos · falhas resolvidas · perguntas respondidas sem roteiro · skills C→B · interviews obtidas · technical rounds atingidas · recurring gaps eliminados.

### Claim matrix — régua de promoção C→B

Uma skill só passa de **C (learning)** para **B (hands-on)** quando o Álvaro consegue: **1)** explicar sem roteiro; **2)** instalar/configurar; **3)** usar em projeto; **4)** provocar falha; **5)** diagnosticar; **6)** recuperar; **7)** explicar tradeoffs; **8)** responder perguntas de entrevista. Só então considerar adicionar ao currículo.

### Carreira em paralelo (não esperar 8 semanas)

- **S1+:** seguir aplicando para Infrastructure / Cloud / Senior DevOps compatível / hands-on infra management.
- **S2+:** incluir vagas com Terraform como requisito complementar.
- **S4+:** incluir vagas DevOps com monitoring.
- **S6+:** incluir SRE-adjacent.

**Job-bot:** relatório semanal *"Top recurring technical gaps among score ≥ 70 jobs"* (tabela skill × % das vagas fortes). Prioridade de estudo = **frequência nas vagas-alvo × importância no papel × tamanho do gap × proximidade de entrevista**. O plano muda conforme esses dados — a weekly review é o momento de ajustar.

### Thread paralela — AWS breadth (P5, da S3 em diante)

2× por semana, no slot de interview prep (~30 min): **EC2 · VPC/subnets/routing · security groups · IAM · S3 · RDS · Route 53 · ALB · CloudWatch · Auto Scaling** — nível interview-ready, não enterprise build-out. Enquadramento sempre honesto e forte: *"Today Satflow runs on Lightsail. At greater scale, I would evaluate…"* — discutir como o ambiente atual **evoluiria**. Consolida no AWS Defense Pack da S8. (O lab de Terraform das S1–S2 já cobre a parte prática de VPC/EC2/SG/S3/IAM.)

---

## Semana 1 — Terraform Foundations (P1)

Objetivo: de "conheço o conceito" para "provisiono recursos básicos com segurança". Lab em conta AWS própria/sandbox — **não** usar a produção da Satmed como primeiro laboratório.

#### S1·D1 — Setup e primeiro apply
- [ ] **Teoria:** IaC e por que declarativo; HCL; providers; ciclo `init` / `plan` / `apply` / `destroy`.
- [ ] **Lab:** instalar Terraform; provider AWS com profile dedicado + billing alarm; primeiro recurso (S3 bucket); `fmt`/`validate` desde o dia 1. Nasce `terraform/lab/`.
- [ ] **Interview:** What is Terraform? Why use IaC?

#### S1·D2 — Variables, outputs, locals, data sources
- [ ] **Teoria:** `variable` (tipos, `sensitive`), `output`, `locals`, `data` sources, interpolação, `.tfvars`.
- [ ] **Lab:** parametrizar o stack; `data` para AMI e AZs em vez de hardcode; um exemplo de `sensitive` e onde ele aparece (e onde não aparece) no output.
- [ ] **Interview:** What is a provider? Resource vs data source? Why shouldn't secrets be hard-coded?

#### S1·D3 — VPC, subnet, security group
- [ ] **Teoria:** grafo de dependências (implícitas vs `depends_on`); como ler um `plan` linha a linha (`+`, `-`, `~`, `-/+`).
- [ ] **Lab:** VPC + subnet + route table + IGW + security group em Terraform.
- [ ] **Interview:** What does `terraform plan` do? — resposta de 60 segundos.

#### S1·D4 — EC2 e o stack completo
- [ ] **Teoria:** key pairs, user data, AMI por `data`; dependências entre SG/subnet/instância.
- [ ] **Lab:** EC2 na VPC do D3, acessível por SSH; `destroy` limpo no fim. O stack completo (VPC/subnet/SG/EC2/S3) sobe e desce com um comando.
- [ ] **Interview:** narrar o que o `apply` fez, recurso por recurso.

#### S1·D5 — Interview day + log
- [ ] As 6 perguntas da semana respondidas **por escrito** em `notes/fte/terraform-interview.md` e em voz alta sem consultar.
- [ ] **Troubleshooting drill:** deletar um recurso pelo console → `plan` → explicar o que o Terraform propõe e por quê.

#### S1·FDS — Althora Fase 0 + consolidação
- [ ] [ALTHORA.md](ALTHORA.md) Fase 0: inventário físico, triagem, decisão ligar/peças/descartar.
- [ ] Refazer o stack da semana do zero, sem consultar os próprios arquivos, em < 45 min.
- [ ] **Ready-for-interview:** ☐ stack do zero sem tutorial ☐ plan explicado linha a linha ☐ resource vs data source e provider sem hesitar ☐ 6 perguntas fluentes.

## Semana 2 — Terraform State, Modules e Real-World Usage (P1)

Objetivo: chegar ao nível em que Terraform pode começar a virar skill **defensável**.

#### S2·D1 — State a fundo
- [ ] **Teoria:** o que o state guarda e por que é sensível; `state list/show/mv/rm`; taint/`-replace`; lifecycle (`create_before_destroy`, `prevent_destroy`, `ignore_changes`).
- [ ] **Lab:** abrir e ler o tfstate; renomear resource com `state mv` sem destruir; forçar recriação com `-replace`; conferir o que um valor `sensitive` vira dentro do state.
- [ ] **Interview:** **What is Terraform state? Why is it sensitive?**

#### S2·D2 — Remote state e locking
- [ ] **Teoria:** por que state local não escala; backend S3; locking (DynamoDB ou S3 native); `init -migrate-state`.
- [ ] **Lab:** migrar o lab para backend S3 com versionamento + criptografia + lock; dois `apply` simultâneos para ver o lock negar; simular lock preso e `force-unlock` sabendo o risco.
- [ ] **Interview:** How do you secure remote state? How do you handle locking?

#### S2·D3 — Modules
- [ ] **Teoria:** anatomia de módulo, inputs/outputs, quando extrair (e quando é overengineering); `for_each` vs `count`; workspaces vs diretório-por-ambiente.
- [ ] **Lab:** refatorar o lab em `terraform/modules/{network,compute,database}` + `envs/dev` consumindo os módulos com `apply` sem mudanças.
- [ ] **Interview:** How do you structure modules? Workspaces or directories — when?

#### S2·D4 — Exercícios de falha (o dia mais importante da fase)
- [ ] **Lab:** provocar e resolver, um por um: **(a)** alteração manual no console → detectar drift (`plan -refresh-only`) → reconciliar nos dois sentidos; **(b)** `import` de recurso criado à mão (import block → plan limpo); **(c)** erro parcial no meio de um apply → entender o estado resultante → recuperar; **(d)** recurso destruído fora do Terraform → recriar.
- [ ] **Interview:** What happens if apply fails halfway? How do you detect drift? How do you import existing infrastructure?

#### S2·D5 — Interview day + Terraform histórico
- [ ] As 8 perguntas obrigatórias da fase (lista abaixo) escritas e cronometradas.
- [ ] **Investigação (§ histórico):** procurar qualquer código Terraform antigo realmente escrito/mantido pelo Álvaro; se existir, documentar data, projeto, recursos, autoria, state, comandos, responsabilidades → só com evidência a claim matrix muda para *B — prior hands-on / refreshed*.

#### S2·FDS — Althora Fase 1–2 + Definition of Done
- [ ] Althora: rede/acesso (Tailscale, SSH por chave) e SO base — **targets prontos para a S3**.
- [ ] **DoD Terraform (checagem honesta):** ☐ escrevo config sem copiar tutorial ☐ uso modules ☐ explico state ☐ uso remote state ☐ explico locking ☐ lido com drift ☐ importo recurso ☐ reviso plan ☐ explico failure handling ☐ discuto segurança. Faltou algum → vira pauta dos próximos fins de semana, o plano segue.

**Perguntas obrigatórias da fase Terraform:** 1. What is Terraform state? 2. Why is state sensitive? 3. How do you secure it? 4. How do you handle locking? 5. How do you detect drift? 6. How do you structure modules? 7. What happens if apply fails halfway? 8. How do you import existing infrastructure?

## Semana 3 — Prometheus (P2)

Objetivo: entender observability na prática, não apenas instalar Prometheus. Targets: hosts do Althora + app FastAPI de lab.

#### S3·D1 — Modelo de métricas e scrape
- [ ] **Teoria:** modelo pull, time series, labels, exposition format, service discovery (estático agora; K8s SD na S7).
- [ ] **Lab:** Prometheus rodando (host Althora ou VM local); scrape dos node_exporters do Althora; explorar targets na UI.
- [ ] **Interview:** Why pull instead of push — trade-offs?

#### S3·D2 — Tipos de métrica e PromQL
- [ ] **Teoria:** counter, gauge, histogram, summary — quando cada um; `rate`, `increase`, `sum by`, `histogram_quantile`.
- [ ] **Lab:** 10 queries escritas à mão sobre os hosts (CPU, memória, disco, rede), salvas comentadas em `observability/promql.md`.
- [ ] **Interview:** Counter vs gauge? Why can't you average percentiles?

#### S3·D3 — Instrumentar a app
- [ ] **Teoria:** método RED para serviços; USE para recursos; o que instrumentar primeiro.
- [ ] **Lab:** FastAPI de lab com `prometheus-client`: request count, latency (histogram), error count, response codes. Séries visíveis no Prometheus.
- [ ] **Interview:** How would you instrument a new service from scratch?

#### S3·D4 — Cardinality e recording rules
- [ ] **Teoria:** cardinality — por que um label `user_id` derruba o Prometheus; recording rules; boas práticas de labels.
- [ ] **Lab:** provocar label explosion de propósito, medir com `prometheus_tsdb_head_series`, corrigir; criar 2 recording rules (error ratio, p95).
- [ ] **Interview:** **What is cardinality and why does it matter?** — com números do próprio experimento.

#### S3·D5 — Troubleshooting day
- [ ] **Lab:** provocar e diagnosticar, um por um: target down · scrape failure (porta/label errados) · label explosion · endpoint lento (medir o impacto no scrape).
- [ ] AWS breadth (thread P5) começa esta semana: EC2 + VPC em profundidade de conversa.

#### S3·FDS — Consolidação
- [ ] Explicar de cabeça o caminho completo: código → `/metrics` → scrape → TSDB → PromQL → resultado.
- [ ] **Ready-for-interview:** ☐ app própria instrumentada ☐ 4 tipos de métrica com exemplo real de cada ☐ `rate()` e `histogram_quantile()` de cabeça ☐ 4 troubleshootings narráveis.

## Semana 4 — Grafana + Alertmanager (P2)

Objetivo: transformar métricas em operação.

#### S4·D1 — Grafana
- [ ] **Teoria:** data sources, dashboards, panels, variables, thresholds, query inspection.
- [ ] **Lab:** Grafana conectada ao Prometheus; primeiro dashboard da app (RED) com variáveis por host/instância.
- [ ] **Interview:** What makes a good dashboard? (orientado a pergunta, não 40 painéis).

#### S4·D2 — Dashboard operacional completo
- [ ] **Lab:** dashboard com **availability, request rate, errors, latency (p50/p95/p99), CPU, memory, disk** — app + hosts Althora; thresholds; export JSON versionado em `observability/dashboards/`.
- [ ] **Interview:** narrar o dashboard como se apresentasse num on-call handoff.

#### S4·D3 — Alertmanager
- [ ] **Teoria:** alert rules vs recording rules; routes, grouping, inhibition, severity; **alert noise vs actionable alerts** — todo alerta exige ação humana, senão é ruído.
- [ ] **Lab:** Alertmanager instalado; rota para canal real (e-mail/Telegram/Slack); um alerta de teste chegando de ponta a ponta.
- [ ] **Interview:** How do you design alerts that don't cause fatigue? Symptom-based vs cause-based?

#### S4·D4 — Os 3 alertas obrigatórios
- [ ] **Lab:** criar e depois **provocar cada condição**: 1) serviço indisponível 2) alta taxa de erro 3) recurso crítico (disco/memória). Anotação `runbook_url` desde já (aponta para o runbook da S6).
- [ ] **Interview:** walk me through what happens from failure to notification.

#### S4·D5 — Interview day + AWS breadth
- [ ] `notes/fte/observability-interview.md` com as Q&A das S3–S4; alerta-que-não-dispara como drill (rule? routing? silence?).
- [ ] AWS breadth: IAM + security groups.

#### S4·FDS — Fire drill + Definition of Done
- [ ] Demo cronometrada: quebrar a app de 3 formas → alerta chega → dashboard aponta → causa confirmada em log. Screenshots guardados para o capstone.
- [ ] **DoD Observability:** ☐ explico metrics/logs/traces ☐ instrumento app ☐ configuro Prometheus ☐ PromQL básica ☐ monto Grafana ☐ crio alertas ☐ reduzo alert noise ☐ diagnostico target down ☐ explico cardinality.

## Semana 5 — Ansible (P3)

Objetivo: automatizar configuração de hosts e reduzir dependência de procedimentos manuais. Lab principal: **hosts do Althora** (reinstaláveis à vontade).

#### S5·D1 — Fundamentos
- [ ] **Teoria:** agentless/SSH, inventories, ad-hoc, playbooks, modules, facts, **idempotency**, `--check`/`--diff`, privilege escalation (`become`).
- [ ] **Lab:** inventory com os hosts Althora; playbook de baseline (users, packages, timezone, SSH hardening); rodar 2× e provar zero changes.
- [ ] **Interview:** What does idempotency mean? What is an inventory?

#### S5·D2 — Variables, templates, handlers
- [ ] **Teoria:** precedência de variáveis (as camadas que importam), Jinja2, handlers/`notify`, conditionals, loops.
- [ ] **Lab:** Nginx configurado por template com variáveis por grupo; handler de reload só quando o template muda (provar com `--diff`); firewall por playbook.
- [ ] **Interview:** What is a handler and why does it run at the end?

#### S5·D3 — Roles
- [ ] **Teoria:** estrutura de role, defaults vs vars, quando extrair role; `ansible-lint`.
- [ ] **Lab:** refatorar em `roles/{base,nginx,app,monitoring}` — a role `monitoring` instala node_exporter direito (substituindo o manual da Fase 2 do Althora); app FastAPI com service file via role `app`; TLS onde apropriado.
- [ ] **Interview:** Role vs playbook?

#### S5·D4 — Vault e CI
- [ ] **Teoria:** `ansible-vault` (arquivo e string; vault password fora do repo); Ansible em CI (lint + `--check`).
- [ ] **Lab:** um secret real via Vault; lint verde no CI (Gitea ou GitHub Actions).
- [ ] **Interview:** How do you handle secrets? Terraform vs Ansible — where's the boundary?

#### S5·D5 — Interview day + AWS breadth
- [ ] `notes/fte/ansible-interview.md` com as 6 perguntas obrigatórias + drills (host unreachable, var indefinida, template inválido).
- [ ] AWS breadth: S3 + RDS.

#### S5·FDS — Teste de fogo + Definition of Done
- [ ] **Reinstalar `althora-02` do zero e reconfigurá-lo 100% por playbook** — zero passos manuais na segunda vez. Documentar o tempo.
- [ ] **DoD Ansible:** ☐ escrevo playbook ☐ inventory ☐ roles ☐ templates ☐ handlers ☐ variables ☐ Vault ☐ explico idempotency ☐ configuro host do zero.

## Semana 6 — SRE e Reliability (P4)

Objetivo: colocar vocabulário formal sobre a experiência operacional que o Álvaro **já tem** (plantão e incident response na Nova, produção na Satmed). Em entrevista: a experiência é real, o vocabulário é o que está sendo formalizado — nunca alegar "SLO em produção" no passado.

#### S6·D1 — SLI, SLO, SLA, error budget
- [ ] **Teoria:** SLI (medida) vs SLO (alvo interno) vs SLA (contrato com consequência); error budget e o que ele compra; availability/latency como SLIs típicos.
- [ ] **Lab:** escolher SatPsy **ou** o lab e definir: SLI (`successful HTTP requests / total requests`), SLO (ex.: 99,9%/30d), **error budget calculado** (99,9% em 30d ≈ 43 min); recording rules que medem de verdade. `sre/slo.md`.
- [ ] **Interview:** SLA vs SLO vs SLI? What does an error budget buy you?

#### S6·D2 — MTTD, MTTR, severity, toil
- [ ] **Teoria:** ciclo do incidente (detect → triage → mitigate → resolve → learn); severity levels; MTTD (encurta com alertas bons) vs MTTR (encurta com runbooks e rollback); on-call; toil; capacity planning básico; reliability vs velocity.
- [ ] **Lab:** `sre/runbook.md` — sintoma → verificação → mitigação para os cenários dos alertas da S4; `runbook_url` agora aponta para algo real.
- [ ] **Interview:** How do you reduce MTTR? What is toil?

#### S6·D3 — Incident simulation (game day)
- [ ] **Lab (dia inteiro):** provocar no Althora/lab, tratando a sério com **incident timeline escrita em tempo real**: application down · node failure · DB connection failure · storage issue. Anotar MTTD e MTTR reais de cada um.
- [ ] Este game day é a resposta de *"tell me about an incident you handled end to end"*.

#### S6·D4 — Blameless postmortem
- [ ] **Teoria:** por que "erro humano" nunca é causa raiz; action items com dono e prazo.
- [ ] **Lab:** postmortem do game day em `sre/postmortems/`; executar pelo menos 1 action item (ex.: o runbook falhou em algo → corrigir).
- [ ] **Interview:** What makes a postmortem blameless and why does that matter?

#### S6·D5 — Interview day + AWS breadth
- [ ] `notes/fte/sre-interview.md`; vocabulário inteiro em voz alta — soar como quem operou, não como quem leu.
- [ ] AWS breadth: Route 53 + ALB + CloudWatch + Auto Scaling.

#### S6·FDS — Backup/recovery + Definition of Done
- [ ] Backup e **restore testado de verdade** de um dado do lab (ex.: Postgres do lab via dump ou o padrão CloudNativePG); `sre/backup.md`.
- [ ] **DoD SRE:** ☐ diferencio SLA/SLO/SLI ☐ calculo error budget ☐ explico MTTR/MTTD ☐ conduzo incident response ☐ escrevo postmortem ☐ discuto reliability vs velocity ☐ identifico toil.

## Semana 7 — Capstone completo

Projeto demonstrável, público, ponta a ponta: **Git → Terraform → AWS → Ansible → Linux → k3s/app containerizada → FastAPI → Prometheus → Grafana → Alertmanager**. O Althora serve de staging; a infra alvo é AWS (é o que as vagas pedem).

#### S7·D1 — Infra (Terraform)
- [ ] Modules + remote state + locking + variables/outputs provisionando VPC + host(s) na AWS. `terraform plan` limpo a partir de clone fresco.

#### S7·D2 — Configuração (Ansible) e app
- [ ] Roles idempotentes configuram o host: base, k3s (ou Docker + compose se k3s não couber no tamanho da instância — decisão documentada), deploy da app FastAPI com `/health` e `/metrics`.

#### S7·D3 — Observability
- [ ] Prometheus + Grafana + Alertmanager no ambiente; dashboard e os 3 alertas portados do lab; service discovery apropriado.

#### S7·D4 — CI/CD e reliability
- [ ] Pipeline: lint/test → infrastructure validation (`fmt`/`validate`/plan) → application deploy. Runbook, backup + recovery testado.

#### S7·D5 — Incident test + documentação
- [ ] Provocar 1 incidente no capstone, seguir o próprio runbook, registrar. README profissional + **architecture diagram** + screenshots (dashboard, alerta, pipeline verde) em `projects/capstone/`.

#### S7·FDS — Prova de reprodutibilidade
- [ ] Do zero num diretório limpo: clone → `terraform apply` → playbook → app monitorada e alertando. Depois `destroy` limpo (custo!). Revisar o repo com olhos de entrevistador; sem secrets no histórico.
- [ ] **Ready:** ☐ capstone reproduzível em uma sessão ☐ diagrama e README que um recruiter técnico entende em 3 min ☐ incidente + postmortem linkados.

## Semana 8 — Interview Hardening

**Nenhuma tecnologia grande nova.** Transformar conhecimento em performance de entrevista: revisar AWS, Linux, Kubernetes, Terraform, CI/CD, networking, databases, Prometheus, Grafana, Ansible, incidents, SRE. Produto central: `career/interview-defense.md` dividido por tópico (os *defense packs*).

#### S8·D1 — AWS + Linux Defense Packs
- [ ] **AWS:** What runs on AWS today? Why Lightsail? How would you migrate to EC2/ECS? Backup? DNS? Security? Monitoring? — sempre ancorado em *Satflow on Lightsail* + a evolução que o Álvaro proporia (thread P5). Nunca inventar enterprise architecture.
- [ ] **Linux:** systemd, journalctl, process troubleshooting, ports, DNS, TLS, disk/memory/CPU, permissions, firewall, Nginx — com 3 exercícios de diagnóstico reais cronometrados no Althora.

#### S8·D2 — Kubernetes Defense Pack (obrigatório — o claim mais forte do currículo)
- [ ] Documentar o ambiente SatPsy: 3-node k3s, topology, Traefik, Longhorn, CloudNativePG, SealedSecrets, NetworkPolicy, registry, networking, storage, upgrades, failure recovery.
- [ ] Responder sem roteiro: Why k3s? What happens if a node dies? How do you upgrade? What is your ingress? How is storage handled? How do you back up Postgres? How are secrets managed? How do you troubleshoot CrashLoopBackOff? ImagePullBackOff? What happens when storage becomes unavailable?
- [ ] As que não tiverem resposta vivida → reproduzir no k3s de lab do Althora antes de responder de cabeça.

#### S8·D3 — Networking + CI/CD Defense Packs
- [ ] **Networking** (precisa ser área forte — Nova/StrataDX): TCP vs UDP, DNS resolution, routing, NAT, CIDR, subnet, gateway, firewall, TLS handshake, HTTP/HTTPS, load balancing, reverse proxy, connectivity troubleshooting.
- [ ] **CI/CD:** Gitea Actions (runners, workflow syntax, build/test/deploy, private registry, Postgres service container, secrets) + GitHub Actions (só projetos reais). Perguntas: secrets? deploy fails? rollback? environments? artifacts? why self-hosted runners?

#### S8·D4 — Database Pack + revisão dos sheets
- [ ] **Database** (sem vender DBA): PostgreSQL backup/restore, users/permissions, connections, common failures, SQL troubleshooting, indexes conceitualmente, logs, disk concerns.
- [ ] Revisar Terraform interview sheet, Observability sheet, SRE sheet — reescrever o que saiu fraco.

#### S8·D5 — Mock interviews
- [ ] 2 sessões cronometradas e **gravadas**: (1) Terraform + Ansible + AWS; (2) Observability + SRE + Kubernetes. + walkthrough do capstone em 5 min: problema → arquitetura → uma decisão difícil → o incidente e o que aprendeu.

#### S8·FDS — Claim matrix, resume e readiness
- [ ] Passar cada skill pela régua C→B (8 critérios) e atualizar a claim matrix **honestamente**; só o que passou entra no currículo.
- [ ] Atualizar resume/LinkedIn (capstone linkado); posicionamento continua **Senior Cloud & Infrastructure Engineer** — agora competitivo para Senior Infrastructure/Cloud/DevOps Engineer, Lead Infrastructure, hands-on manager e SRE-adjacent. Nunca "acabou de fazer um curso de DevOps".
- [ ] **Relatório final de readiness:** o que virou B, o que segue C, os 3 gaps restantes → plano do próximo ciclo, informado pelo job-bot.

---

## Não estudar agora

Advanced Go · Kubernetes operators · service mesh profundo · advanced platform engineering · multi-cloud certification · PMP · Scrum certification · random cloud badges · frontend · ML/AI engineering. Só entra se os dados do funil (job-bot) justificarem.

**Certificações:** nada iniciado só pelo selo. Reavaliar após o ciclo: **CKA** se o mercado responder bem às vagas Kubernetes e o custo/tempo couber; **AWS cert** se o job-bot mostrar forte recorrência e recruiters valorizarem. Certificação nunca substitui experiência.

## Deliverables do ciclo (checklist final)

1. ☐ este plano detalhado · 2. ☐ agenda diária cumprida (study-log) · 3. ☐ exercícios · 4. ☐ labs · 5. ☐ repo do capstone · 6. ☐ architecture diagram · 7. ☐ runbook · 8. ☐ incident simulation · 9. ☐ postmortem · 10. ☐ Terraform interview sheet · 11. ☐ Kubernetes defense pack · 12. ☐ AWS defense pack · 13. ☐ Linux defense pack · 14. ☐ CI/CD defense pack · 15. ☐ Observability defense pack · 16. ☐ SRE interview sheet · 17. ☐ claim matrix atualizada · 18. ☐ relatório final de readiness.

## Convenções

- **Commits:** `fte sN.dN: <tema> — <entregável>`. **Notas:** `notes/fte/` (interview sheets) + `career/study-log.md` (diário) + `career/interview-defense.md` (packs).
- **Custo AWS:** billing alarm ativo; `destroy` em tudo que é pago e ocioso; NAT Gateway/EKS/RDS nunca ficam de pé sem uso.
- **Segurança:** nenhum secret/credencial no repo (que fica público na S8 — trate como público desde já); produção SatPsy/Satflow **nunca** é laboratório.
- **Althora:** estratégia e fases em [ALTHORA.md](ALTHORA.md); manutenção do lab não pode comer horas de estudo.
