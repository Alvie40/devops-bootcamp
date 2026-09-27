# Isolamento de containers: namespaces + cgroups

> Container não é uma coisa que existe no kernel. É um **processo comum** que o runtime
> (runc) prende com três mecanismos:
>
> | Mecanismo | Controla | Pergunta |
> |---|---|---|
> | **namespaces** | visão | *o que o processo enxerga?* |
> | **cgroups** | consumo | *quanto ele pode usar?* |
> | **capabilities + seccomp + LSM** | permissão | *o que ele pode fazer?* |

## Como rodar no Mac

O macOS não tem namespaces nem cgroups. O Docker Desktop roda uma VM Linux (kernel
6.12, cgroup v2), e o `lab.sh` abre um Ubuntu **privilegiado** dentro dela que enxerga a
árvore real de cgroups. É a nossa "máquina Linux" descartável.

```bash
./lab.sh                         # shell interativo no lab
./lab.sh 01-namespaces.sh        # roda um exercício (PAUSE=1 para ir passo a passo)
./04-docker-por-dentro.sh        # 04 e 05 rodam direto no Mac
```

| # | Onde | O que prova |
|---|---|---|
| 01 | lab | cada namespace isolado com `unshare`; `nsenter` = `docker exec` |
| 02 | lab | cgroup v2 na mão: OOM kill (137), fork bomb contida, throttling de CPU |
| 03 | lab | "container" sem Docker: rootfs do Alpine + 7 namespaces + cgroup |
| 04 | Mac | `--memory/--cpus/--pids-limit` viram arquivos em `/sys/fs/cgroup/docker/<id>/` |
| 05 | Mac | onde o isolamento **acaba**: kernel, `/proc`, capabilities, seccomp, `--privileged` |

## Namespaces

Cada processo aponta para um namespace de cada tipo em `/proc/<pid>/ns/`. Criar um novo
(`unshare`, `clone`) dá ao processo uma cópia privada daquele recurso.

| Namespace | Isola | Efeito no container |
|---|---|---|
| `pid` | árvore de processos | o app é PID 1; não vê processos do host |
| `mnt` | pontos de montagem | filesystem próprio (rootfs da imagem) |
| `net` | interfaces, rotas, iptables, portas | IP próprio; liga ao host por veth + bridge |
| `uts` | hostname | `hostname` = ID do container |
| `ipc` | filas/semáforos System V, POSIX mq | não conversa por IPC com vizinhos |
| `user` | UIDs/GIDs | root dentro ≠ root fora (**desligado por padrão no Docker**) |
| `cgroup` | visão da árvore de cgroup | enxerga o próprio cgroup como `/` |
| `time` | CLOCK_MONOTONIC/BOOTTIME | quase ninguém usa |

Pontos de entrevista:

- **PID 1 é especial**: não recebe sinais sem handler explícito (SIGTERM é ignorado) e, se
  morre, o kernel mata o namespace inteiro. Daí `tini`/`--init` e o `docker stop` que
  demora 10 s.
- **`docker exec` = `nsenter`**: entra nos namespaces de um processo que já existe.
- **Pod no Kubernetes** = containers que **compartilham** net, ipc e uts (via container
  *pause*). Por isso falam por `localhost`.
- **`--net=host`, `--pid=host`**: simplesmente *não* criar aquele namespace.

## cgroups v2

Uma única árvore montada em `/sys/fs/cgroup`. **Diretório = grupo, arquivo = interface.**
Escrever um PID em `cgroup.procs` move o processo; os filhos herdam.

| Arquivo | Significado | Docker | Kubernetes |
|---|---|---|---|
| `memory.max` | teto rígido; passou → OOM kill | `--memory` | `limits.memory` |
| `memory.high` | freio suave (reclaim agressivo) | — | (MemoryQoS) |
| `memory.swap.max` | swap permitido | `--memory-swap` | — |
| `cpu.max` | cota `usec período` (CFS bandwidth) | `--cpus` | `limits.cpu` |
| `cpu.weight` | prioridade relativa sob disputa | `--cpu-shares` | `requests.cpu` |
| `pids.max` | máximo de tarefas | `--pids-limit` | `podPidsLimit` |
| `io.max` | limite de IOPS/banda por device | `--device-*-bps` | — |

Métricas para diagnóstico: `memory.events` (`oom_kill`), `memory.peak`, `cpu.stat`
(`nr_throttled`, `throttled_usec`), `pids.events`.

- **Exit 137** = 128 + 9 (SIGKILL) → quase sempre OOM do cgroup.
- **CPU throttling**: o processo usa a cota no começo do período de 100 ms e fica parado
  até o próximo. A latência p99 sobe sem a CPU parecer cheia. Por isso muita gente usa
  `requests` sem `limits` de CPU.
- **Memória não é compressível, CPU é**: estourar memória mata; estourar CPU só atrasa.

## Onde o isolamento acaba (05)

1. **Kernel compartilhado.** Todo container faz syscalls no mesmo kernel; uma CVE de kernel
   quebra todos. VM (ou gVisor/Kata/Firecracker) põe outro kernel no meio.
2. **`/proc` não é virtualizado.** `free`, `nproc` e `/proc/meminfo` mostram o host. O app
   precisa ler o cgroup (JVM ≥ 10 e Go ≥ 1.25 já leem; LXCFS é outro remédio).
3. **Root no container é uid 0 no host** sem user namespace. Só as capabilities (≈14 de
   41) e o seccomp seguram. Rootless Docker/Podman e `userns-remap` corrigem.
4. **`--privileged`** = todas as capabilities, sem seccomp/AppArmor, `/dev` do host
   visível → `mount /dev/vda1` e acabou. Montar `docker.sock` é equivalente a root no host.
   (O próprio lab provou isso: o cgroup criado dentro do container continuou existindo na VM
   depois que o container morreu.)

Hardening que fecha as brechas: usuário não-root na imagem, `--cap-drop ALL` + só o que
precisa, `--read-only`, `no-new-privileges`, perfil seccomp padrão (nunca `unconfined`),
AppArmor/SELinux, user namespaces, e runtime com sandbox para código não confiável.

## Referências

- `man 7 namespaces`, `man 7 cgroups`, `man 7 capabilities`, `man 1 unshare`, `man 1 nsenter`
- Documentação do kernel: `Documentation/admin-guide/cgroup-v2.rst`
