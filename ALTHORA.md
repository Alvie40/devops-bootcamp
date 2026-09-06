# Althora Data Center — estratégia de religamento

Plano para tirar o home lab (Needham, MA) do estado **desligado** e transformá-lo no laboratório permanente do [ROADMAP-FTE.md](ROADMAP-FTE.md). O Althora não é um projeto paralelo: cada fase daqui existe para servir uma semana do plano de estudos — se uma decisão não acelera o FTE, ela é adiada.

**Papel do Althora no plano:**

| Semana do plano | O que o Althora fornece |
|---|---|
| S3–S4 (Prometheus/Grafana) | Hosts reais para node_exporter, dashboards de CPU/mem/disk e alertas — sem custo de cloud |
| S5 (Ansible) | **O laboratório principal**: hosts Linux configurados do zero por roles, reinstaláveis à vontade |
| S6 (SRE) | Palco dos incident simulations: matar node, encher disco, derrubar DB — sem tocar produção |
| S7 (Capstone) | Ambiente de staging/failure-testing complementar ao capstone AWS |
| Entrevistas | História concreta de on-prem + cloud: hardware, rede, DNS, virtualização, monitoring |

**O que o Althora NÃO é:** substituto do lab AWS (Terraform nas S1–S2 é AWS, porque é o que as vagas pedem) e não é dependência crítica — se um hardware não subir, o plano segue com VMs locais (UTM/Multipass no macOS) ou instâncias pequenas na AWS. O Althora é acelerador, não bloqueador.

---

## Fase 0 — Inventário e triagem (fim de semana antes da S1, ou o primeiro)

Está tudo desligado, então o primeiro passo é físico, não técnico. Nada de decidir stack antes de saber o que existe e o que ainda funciona.

- [ ] Inspeção física: listar cada máquina, fonte, switch, cabo, nobreak. Fotografar antes de mexer.
- [ ] Preencher o inventário abaixo em `homelab/inventory.md` (este arquivo vira a fonte da verdade).
- [ ] Ligar uma máquina por vez, fora da rede: POST ok? Ventoinhas? BIOS acessível? Relógio/bateria CMOS?
- [ ] Discos: `smartctl -a` em cada um (live USB serve). Disco com pending/reallocated sectors não guarda nada que importe.
- [ ] Decidir o destino de cada máquina: **ligar** / **peças** / **descartar**. Critério: mínimo 2 hosts utilizáveis com 8 GB+ RAM cada; o resto é bônus.
- [ ] Estimar custo de energia e decidir o que fica 24/7 vs sob demanda: `custo/mês ≈ watts × 0,72 × $/kWh` (MA ≈ $0,30/kWh → um host de 100 W ≈ $22/mês). Medir com kill-a-watt se disponível.
- [ ] Checar térmica e ruído do local — hardware que esquenta ou incomoda a casa acaba desligado de novo em duas semanas.

**Template do inventário** (`homelab/inventory.md`):

```markdown
| Host        | Modelo | CPU | RAM | Discos (modelo/SMART) | NIC | Estado | Destino |
|-------------|--------|-----|-----|-----------------------|-----|--------|---------|
| althora-01  |        |     |     |                       |     |        |         |
```

**Critério de saída da Fase 0:** inventário preenchido + pelo menos 2 hosts que dão POST com disco confiável. Se não houver 2 hosts viáveis, registrar isso e ativar o plano B (VMs locais) sem gastar mais fins de semana em hardware morto.

## Fase 1 — Rede e acesso (durante S1–S2, blocos de fim de semana)

Objetivo: hosts acessíveis por SSH de qualquer lugar, sem expor nada à internet.

- [ ] Endereçamento: reservas DHCP no roteador (ou faixa estática) num bloco dedicado — documentar CIDR escolhido no inventário. Se o roteador suportar VLAN, segmento próprio separado da rede da família; se não, pelo menos faixa reservada + firewall nos hosts.
- [ ] Convenção de nomes: `althora-01`, `althora-02`, … — os mesmos nomes no inventário, no DNS local e depois no inventory do Ansible.
- [ ] Acesso remoto: **Tailscale** (ou WireGuard) em cada host. **Nenhuma porta de gerência exposta à internet, nunca** — nada de port-forward de SSH.
- [ ] SSH: só chave, `PermitRootLogin no`, usuário pessoal + sudo. (Na S5 isso tudo vira role do Ansible — por enquanto, manual e anotado.)
- [ ] DNS local simples (entradas no Tailscale/MagicDNS resolve isso de graça).

**Critério de saída:** `ssh althora-01` funciona do MacBook de qualquer rede; diagrama de rede de 1 tela (mesmo à mão) commitado em `homelab/`.

## Fase 2 — Sistema base (até o fim da S2)

Deadline importa: a S3 (Prometheus) precisa de targets prontos.

- [ ] **Decisão de plataforma — regra simples:** hosts pequenos/médios → **Ubuntu LTS bare metal** (menos camadas, é o que as vagas pedem). Se houver UMA máquina grande (32 GB+), **Proxmox nela** para criar VMs descartáveis de lab (cenários de reinstalação infinitos para o Ansible). Não virtualizar por hobby — só se multiplicar cenários de estudo.
- [ ] Instalar o SO base anotando cada passo manual — essa anotação é literalmente o backlog das roles da S5.
- [ ] `node_exporter` em cada host (pode ser instalação manual agora; a role `monitoring` da S5 refaz isso direito).
- [ ] Snapshot do estado: `homelab/inventory.md` atualizado com IPs, SO, função de cada host.

**Critério de saída:** 2+ hosts com Ubuntu atualizado, acessíveis via Tailscale, expondo `:9100/metrics`.

## Fase 3 — Serviço ao plano de estudos (S3 em diante)

A partir daqui o Althora não tem mais fases próprias — ele é consumido pelo roadmap:

- **S3:** Prometheus (rodando num host do Althora ou em VM local) raspando os node_exporters + a app FastAPI de lab.
- **S4:** Grafana + Alertmanager no mesmo lugar; os 3 alertas obrigatórios do plano são provocados **nestes hosts** (derrubar serviço, injetar erro, encher disco).
- **S5:** o teste de fogo do Ansible — reinstalar `althora-02` do zero e reconfigurá-lo 100% por playbook (`base`, `nginx`, `app`, `monitoring`). Zero passos manuais na segunda vez.
- **S6:** game day — node failure, DB connection failure, storage issue, com timeline e postmortem de verdade.
- **S7:** staging do capstone: ensaiar aqui o que depois sobe na AWS; k3s de lab se quiser praticar upgrade/recuperação sem risco (a produção SatPsy na Hostinger **nunca** é lab).

## Segurança e princípios permanentes

- Nada do Althora exposto à internet; acesso só por Tailscale/WireGuard.
- Nenhum secret em texto plano no repo — o lab segue as mesmas regras do resto do plano (Vault/SealedSecrets/SSM quando chegar a hora).
- Rede do lab isolada da rede da família na medida do que o roteador permitir.
- Dado que importa não mora no lab: tudo ali deve ser destruível e recriável — essa é a graça.
- Se a manutenção do lab começar a comer horas de estudo (hardware velho falhando toda semana), degradar para plano B sem culpa: o objetivo é o FTE, não o uptime do porão.

## Ângulo de entrevista (sem sobrevender)

O Althora rende respostas fortes se descrito com precisão: *"I run a small home datacenter that I use as a lab — bare-metal Linux, segmented network, WireGuard access, configured entirely by Ansible roles, monitored by Prometheus/Grafana; I use it to rehearse failure scenarios before touching production."* Isso é demonstrável e verdadeiro. **Não** chamá-lo de "datacenter que opero para clientes" nem inflar para enterprise — a força está em ser real, reconstruível e monitorado.
