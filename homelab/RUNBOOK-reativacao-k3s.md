# Runbook — reativação do k3s no Althora

Objetivo: religar um cluster k3s multi-nó que está fisicamente desligado há um tempo
indeterminado, com o mínimo de surpresa. Ordem importa mais do que velocidade — cada
etapa só avança depois que a anterior confirmou saúde.

Preencher [inventory.md](inventory.md) com os dados reais conforme forem aparecendo
(hostname, papel, IP Tailscale) — esse arquivo hoje está vazio.

## 0. Antes de ligar qualquer coisa

- [ ] Confirmar qual é o **papel de cada nó**: 1 server + N agents, ou HA com embedded
      etcd (múltiplos servers)? Isso decide a ordem da seção 2. Se não lembrar,
      `cat /etc/systemd/system/k3s.service` (tem `server` no `ExecStart`?) ou
      `/etc/systemd/system/k3s-agent.service` (é agent) resolve assim que o primeiro
      nó subir.
- [ ] Inspeção física rápida (não precisa da Fase 0 inteira do ALTHORA.md, mas o
      mínimo): poeira/umidade visível, cabos de força e rede firmes, sem cheiro de
      queimado. Se ficou meses desligado, checar bateria CMOS mentalmente — relógio
      pode ter zerado, o que quebra TLS (seção 3).
- [ ] **Risco #1, decorar antes de começar:** certificados TLS do k3s (server e
      kubelet) por padrão expiram 12 meses após emissão. Cluster desligado há mais de
      ~1 ano quase certamente volta com certs vencidos — o serviço sobe mas os nós não
      se enxergam. Não é bug, é esperado; procedimento na seção 4 se acontecer.

## 1. Rede primeiro, k3s depois

Ligar as máquinas ainda não resolve nada se a rede não voltar — e sem rede não dá pra
diagnosticar remotamente.

- [ ] Ligar **um nó por vez**, começando pelo que provavelmente é o server/control-plane.
      Esperar POST completo antes do próximo.
- [ ] Por nó: `ssh althora-0X` via Tailscale. Se falhar:
  - `tailscale status` no Mac — o nó aparece na lista, mesmo offline?
  - Se o nó não aparece: pode ter perdido a config de rede local (DHCP mudou, roteador
    trocou) — nesse caso precisa de acesso local (teclado/monitor ou console) pra essa
    única vez, não é falha do Tailscale.
  - Se aparece mas não conecta: `sudo tailscale up` localmente no nó (via console) pode
    ter expirado a chave de auth — reautenticar.
- [ ] Confirmar hora do sistema em cada nó: `timedatectl`. Se o relógio estiver muito
      errado (bateria CMOS morta), `sudo timedatectl set-ntp true` e esperar sincronizar
      **antes** de tocar no k3s — TLS é sensível a clock skew além do problema de certs
      vencidos.

**Critério de saída:** `ssh` funcionando em todos os nós, hora sincronizada. Não passar
pra seção 2 com rede pela metade.

## 2. Subir o k3s — ordem importa

- [ ] **Se 1 server + N agents:** subir o server primeiro (`sudo systemctl start k3s`),
      confirmar saudável (`sudo systemctl status k3s`, `sudo k3s kubectl get nodes` —
      só ele deve aparecer, `Ready`), só então subir os agents
      (`sudo systemctl start k3s-agent` em cada um, um de cada vez).
- [ ] **Se HA com embedded etcd (múltiplos servers):** etcd precisa de quorum —
      maioria dos servers no ar (2 de 3). Subir os servers primeiro, um de cada vez,
      olhando `sudo journalctl -u k3s -f` no primeiro pra ver se ele espera pelos
      outros. Não subir agents antes do quorum de etcd estar de pé.
- [ ] Depois de cada `systemctl start`, olhar o log antes de assumir sucesso:
      `sudo journalctl -u k3s -n 50 --no-pager` (ou `k3s-agent`). "Serviço ativo" no
      systemd não significa cluster saudável — k3s sobe o processo mesmo travado
      tentando conectar em algo.

**Critério de saída:** `kubectl get nodes` mostra todos os nós esperados em `Ready`.

## 3. Validar o cluster, não só o processo

- [ ] `kubectl get pods -A` — tudo em `Running`/`Completed`? Prestar atenção em
      `coredns`, `traefik` (ou o ingress usado), e qualquer storage provisioner
      (Longhorn, se este lab espelhar o setup do SatPsy).
- [ ] Se houver storage persistente no lab: `kubectl get pvc -A` e `kubectl get pv` —
      volumes remontaram ou ficaram `Pending`/`Lost`? Disco que ficou desligado meses
      pode ter saído da lista de replicas do Longhorn.
- [ ] Testar um deploy trivial (`kubectl run test --image=nginx --rm -it -- true` ou
      similar) pra confirmar que o scheduler e o CNI estão de fato funcionais, não só
      que a API responde.
- [ ] Atualizar [inventory.md](inventory.md) com o estado real encontrado (papel de
      cada nó, IP, o que precisou de conserto).

## 4. Se os certificados estiverem vencidos (risco #1 da seção 0)

Sintoma: `journalctl -u k3s` mostra erro de TLS/certificate expired; nós não se juntam
mesmo com rede e hora OK.

- [ ] k3s tem rotação embutida: `sudo k3s certificate rotate` no server, depois
      `sudo systemctl restart k3s`. Cobre os certs de curto prazo.
- [ ] Se o cert da **CA** em si expirou (cluster muito parado, >1 ano): é o caso mais
      chato — precisa de `k3s certificate rotate-ca` com o cluster parado e backup do
      datastore antes. Não improvisar isso ao vivo sem ler a doc oficial do k3s pra
      versão instalada (`k3s --version`) primeiro; comportamento mudou entre versões.
- [ ] Alternativa mais simples se o cluster é só de lab e não guarda nada crítico:
      aceitar a perda, reinstalar k3s do zero nesse nó (`k3s-uninstall.sh` +
      reinstalar) em vez de brigar com rotação de CA. Mais rápido que debugar, e o
      objetivo aqui é ter um lab funcional pra estudar, não recuperar dado.

## 5. Depois de reativado

- [ ] Entrada no `career/study-log.md` no formato padrão (What I built / What broke /
      How I fixed it / Interview questions) — isso é material direto pro Kubernetes
      Defense Pack ([interview-defense.md](../career/interview-defense.md)): "o que
      acontece quando o nó fica offline por meses" é pergunta real de entrevista e
      agora vai ter resposta vivida, não hipotética.
- [ ] Preencher a pergunta 2 da tabela do defense pack ("What happens if a node dies?")
      com o que foi observado aqui, se fizer sentido — reativação depois de meses
      desligado é uma variante realista desse cenário.
