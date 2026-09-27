#!/usr/bin/env bash
# Roda NO MAC. Onde o isolamento de container acaba. Container != VM.
set -euo pipefail
cyan=$'\e[36m'; dim=$'\e[2m'; bold=$'\e[1m'; reset=$'\e[0m'
run() { printf '%s$ %s%s\n' "$cyan" "$1" "$reset"; bash -c "$1" 2>&1 || true; echo; }
nota() { printf '%s# %s%s\n' "$dim" "$1" "$reset"; }
t() { printf '\n%s== %s ==%s\n' "$bold" "$1" "$reset"; }

t "1. Kernel compartilhado"
nota "Todo container usa o kernel do host. Bug de kernel = fuga para todos. VM tem kernel próprio."
run "docker run --rm alpine:3.20 uname -r; docker run --rm ubuntu:24.04 uname -r"

t "2. /proc mente sobre recursos"
nota "Limite de 64M, mas free e /proc/meminfo mostram a memória da VM inteira."
nota "Apps que dimensionam heap/threads lendo isso (JVM antiga, Node, runtimes) erram. Leia o cgroup."
run "docker run --rm --memory 64m alpine:3.20 sh -c 'free -m | head -2; echo; echo cgroup diz: \$(cat /sys/fs/cgroup/memory.max)'"
run "docker run --rm --cpus 0.5 alpine:3.20 sh -c 'echo nproc: \$(nproc); echo cpu.max: \$(cat /sys/fs/cgroup/cpu.max)'"
nota "nproc vê todos os cores, mas a cota é meio core. Runtime que cria 1 thread/worker por core"
nota "(Go antes do 1.25 com GOMAXPROCS, pools de thread) vai sofrer throttling pesado."

t "3. Capabilities: root no container é root 'podado'"
nota "O root do Linux é quebrado em ~41 capabilities. O Docker entrega só ~14 por padrão."
run "docker run --rm alpine:3.20 sh -c 'grep CapEff /proc/self/status'"
run "docker run --rm --privileged alpine:3.20 sh -c 'grep CapEff /proc/self/status'"
nota "Sem CAP_SYS_ADMIN, mount falha. É isso que impede o container de montar o disco do host:"
run "docker run --rm alpine:3.20 mount -t tmpfs tmpfs /mnt"
run "docker run --rm --cap-drop ALL alpine:3.20 chown nobody /etc/hostname"

t "4. seccomp: filtro de syscalls"
nota "Seccomp: 2 = modo filtro ativo. O perfil padrão do Docker bloqueia ~40+ syscalls (unshare, keyctl, ...)."
run "docker run --rm alpine:3.20 grep Seccomp /proc/self/status"
run "docker run --rm alpine:3.20 unshare --user id"
run "docker run --rm --security-opt seccomp=unconfined alpine:3.20 grep Seccomp /proc/self/status"

t "5. --privileged desliga quase tudo"
nota "Todas as capabilities, sem seccomp, sem AppArmor, /dev inteiro do host visível."
run "docker run --rm alpine:3.20 sh -c 'ls /dev | wc -l'"
run "docker run --rm --privileged alpine:3.20 sh -c 'ls /dev | wc -l; ls /dev | grep -E \"^(vd|sd|nvme)\" | head -3'"
nota "Com --privileged, 'mount /dev/vda1 /mnt' dá acesso ao disco do host. É a fuga clássica."
nota "O próprio lab.sh deste diretório provou: o cgroup 'lab' sobreviveu ao container porque"
nota "escrevemos na árvore real da VM. Por isso --privileged e docker.sock nunca vão pra produção."

t "6. User namespace (o que o Docker NÃO usa por padrão)"
run "docker run --rm alpine:3.20 sh -c 'cat /proc/self/uid_map'"
nota "'0 0 4294967295' = mapeamento identidade: uid 0 dentro é uid 0 fora."
nota "Com userns-remap ou rootless, uid 0 dentro vira ex. 100000 fora. Fuga cai como usuário sem poder."

t "Resumo: camadas de defesa"
nota "namespaces (o que vê) + cgroups (o quanto usa) + capabilities + seccomp + LSM (o que pode fazer)"
nota "+ user ns (quem é de verdade) + read-only rootfs + non-root user. Mais forte: gVisor, Kata, Firecracker."
