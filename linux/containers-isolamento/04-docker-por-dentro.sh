#!/usr/bin/env bash
# Roda NO MAC (não no lab). Mostra que flags do docker viram arquivos de cgroup e
# que um container é só um processo com namespaces diferentes.
set -euo pipefail
cyan=$'\e[36m'; dim=$'\e[2m'; bold=$'\e[1m'; reset=$'\e[0m'
run() { printf '%s$ %s%s\n' "$cyan" "$1" "$reset"; bash -c "$1"; echo; }
nota() { printf '%s# %s%s\n' "$dim" "$1" "$reset"; }

NAME=alvo-cg
docker rm -f $NAME >/dev/null 2>&1 || true
trap 'docker rm -f $NAME >/dev/null 2>&1' EXIT

printf '\n%s== 1. Container com limites ==%s\n' "$bold" "$reset"
run "docker run -d --name $NAME --memory 64m --memory-swap 64m --pids-limit 15 --cpus 0.5 alpine:3.20 sleep 300"

printf '%s== 2. Onde o Docker gravou isso ==%s\n' "$bold" "$reset"
nota "--pid=host deixa o container 'espião' ver os processos da VM; privileged + cgroupns=host veem a árvore real."
SPY="docker run --rm --privileged --pid=host --cgroupns=host alpine:3.20"
CID=$(docker inspect -f '{{.Id}}' $NAME)
run "$SPY sh -c 'cd \$(find /sys/fs/cgroup -maxdepth 3 -type d -name \"*$CID*\" | head -1) && pwd && for f in memory.max memory.swap.max pids.max cpu.max; do printf \"%-16s %s\n\" \$f \"\$(cat \$f)\"; done'"
nota "--memory 64m -> 67108864 bytes; --cpus 0.5 -> '50000 100000'; --pids-limit 15 -> 15."

printf '%s== 3. Container = processo com outros namespaces ==%s\n' "$bold" "$reset"
PID=$(docker inspect -f '{{.State.Pid}}' $NAME)
nota "PID do container na VM: $PID. Compare os inodes com os do PID 1 da VM."
run "$SPY sh -c 'for ns in pid net mnt uts ipc cgroup user; do printf \"%-7s vm=%-22s container=%s\n\" \$ns \$(readlink /proc/1/ns/\$ns) \$(readlink /proc/$PID/ns/\$ns); done'"
nota "Repare: user é IGUAL. Por padrão o Docker não usa user namespace -> root no container é uid 0 no host."

printf '%s== 4. docker exec = nsenter ==%s\n' "$bold" "$reset"
run "$SPY nsenter -t $PID -u -p -m -n hostname"
run "docker exec $NAME hostname"
