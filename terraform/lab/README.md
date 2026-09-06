# Lab Terraform — S1·D1: setup e primeiro apply

Missão do dia (~90 min). Spec, não tutorial — o código é seu. Consultas permitidas: docs oficiais da HashiCorp/AWS e os vídeos da S1. Proibido: copiar main.tf pronto de repo alheio.

## 0. Segurança primeiro (bloqueante)

- [ ] Confirmar que a conta do profile `default` (account ID e user ficam no seu `~/.aws/credentials`, fora do repo) **não** é a produção Satflow/Satmed. Se for: criar IAM user `terraform-lab` (access key própria) e profile dedicado `lab` no `~/.aws/config`; todo o lab usa `--profile lab` / `AWS_PROFILE=lab`.
- [ ] Billing alarm ativo na conta do lab (CloudWatch billing alarm, ex.: $10). Não seguir sem isso.

## 1. Primeiro recurso

- [ ] `main.tf` com: `terraform` block (required_version, required_providers), provider `aws` (região + profile do lab).
- [ ] Um bucket S3 com nome único e tags (`Project = "fte-lab"`).
- [ ] Ciclo completo, lendo a saída de cada passo: `init` → `fmt` → `validate` → `plan` → `apply` → olhar no console → `destroy`.

## 2. Segundo recurso

- [ ] Um security group (ingress 22 e 443, egress all) — recriar com `apply`, examinar o `plan` linha a linha e explicar cada símbolo (`+`, `-`, `~`).
- [ ] Abrir o `terraform.tfstate` num editor e identificar: o que ele guarda sobre o bucket? Por que este arquivo é sensível?

## Definition of Done do dia

- [ ] `terraform apply` e `destroy` limpos, executados mais de uma vez.
- [ ] Explicar em voz alta, 60s cada, sem consultar: *What is Terraform? Why IaC? What does `plan` do?*
- [ ] Entrada de hoje preenchida em `career/study-log.md` (principalmente "what broke").
- [ ] Commit: `fte s1.d1: terraform — primeiro apply (s3 + sg)`.

## Nota

`.gitignore` do repo já deve cobrir `*.tfstate`, `*.tfstate.*`, `.terraform/` e `*.tfvars` — confirmar com `git status` antes do commit.
