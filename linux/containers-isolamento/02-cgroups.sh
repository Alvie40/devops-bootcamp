#!/usr/bin/env bash
# cgroups v2: o quanto o processo pode USAR.
source "$(dirname "$0")/_lib.sh"

CG=/sys/fs/cgroup/lab
trap 'for p in $(cat $CG/cgroup.procs 2>/dev/null); do kill -9 $p 2>/dev/null; done; sleep 0.2; rmdir $CG 2>/dev/null' EXIT

titulo "1. cgroup v2 é um filesystem"
nota "Uma árvore só (unified hierarchy). Diretório = grupo; arquivo = controle ou métrica."
run 'stat -fc %T /sys/fs/cgroup; cat /sys/fs/cgroup/cgroup.controllers'
nota "subtree_control = quais controllers os FILHOS podem usar."
run 'cat /sys/fs/cgroup/cgroup.subtree_control'

titulo "2. Criar um cgroup = mkdir"
run "mkdir -p $CG && ls -C -w 100 $CG | head -12"

titulo "3. memory.max: passou do limite, o kernel mata (OOM)"
run "echo 50M > $CG/memory.max; echo 0 > $CG/memory.swap.max; cat $CG/memory.max"
nota "Mover um processo = escrever o PID em cgroup.procs. Filhos herdam o cgroup."
nota "'tail /dev/zero' guarda a 'linha' inteira na memória e nunca acha o \\n: come RAM sem parar."
run "bash -c 'echo \$\$ > $CG/cgroup.procs; exec tail /dev/zero'; echo \"exit=\$? (137 = 128 + SIGKILL 9)\""
run "grep -E 'oom|max' $CG/memory.events; echo pico: \$(( \$(cat $CG/memory.peak) / 1024 / 1024 ))MB"
nota "No Kubernetes isso aparece como 'OOMKilled' com exit code 137."

titulo "4. pids.max: fork bomb contida"
run "echo 20 > $CG/pids.max"
run "bash -c 'echo \$\$ > $CG/cgroup.procs; for i in \$(seq 100); do sleep 3 & done 2>&1 | sort | uniq -c; wait'"
run "cat $CG/pids.events; echo pico: \$(cat $CG/pids.peak)"

titulo "5. cpu.max: cota de CPU (CFS bandwidth)"
nota "'20000 100000' = 20ms de CPU a cada período de 100ms = 20% de 1 core."
run "echo '20000 100000' > $CG/cpu.max"
run "bash -c 'echo \$\$ > $CG/cgroup.procs; timeout 3 sh -c \"while :; do :; done\"'"
run "grep -E 'usage_usec|nr_periods|nr_throttled|throttled_usec' $CG/cpu.stat"
nota "3s de relógio -> ~0.6s de CPU. nr_throttled > 0 é o sinal de CPU limit apertado:"
nota "latência sobe sem a CPU parecer 'cheia'. É o motivo de muita gente não pôr CPU limit no k8s."

titulo "6. cpu.weight: não é limite, é prioridade relativa sob disputa"
nota "Padrão 100. Só importa quando há contenção; com CPU sobrando, ninguém é freado."
nota "No k8s, requests.cpu vira cpu.weight e limits.cpu vira cpu.max."
run "cat $CG/cpu.weight"

titulo "7. De onde vem o cgroup de qualquer processo"
run 'cat /proc/self/cgroup'
nota "Veja no 04 como o Docker cria um cgroup por container e escreve esses mesmos arquivos."
