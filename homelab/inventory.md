# Inventário — Althora home lab (Needham, MA)

Fonte da verdade do hardware físico (ver [ALTHORA.md](../ALTHORA.md) Fase 0). Preencher
durante a reativação do k3s — este arquivo nasceu vazio porque a Fase 0 nunca foi
registrada, embora o k3s já tenha sido instalado antes.

| Host | Papel k3s | Modelo | CPU | RAM | Discos (modelo/SMART) | NIC / IP Tailscale | Estado atual | Notas |
|------|-----------|--------|-----|-----|------------------------|---------------------|---------------|-------|
| althora-01 | ? (server/agent) | | | | | | desligado | |
| althora-02 | ? (server/agent) | | | | | | desligado | |
| althora-03 | ? (server/agent) | | | | | | desligado | |

**Papel k3s:** confirmar antes de religar — se é 1 server + N agents, ou HA com
embedded etcd (múltiplos servers). Isso muda a ordem de boot no
[RUNBOOK-reativacao-k3s.md](RUNBOOK-reativacao-k3s.md).
