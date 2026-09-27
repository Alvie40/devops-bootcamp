#!/usr/bin/env bash
# Namespaces: o que o processo ENXERGA.
source "$(dirname "$0")/_lib.sh"

titulo "1. Todo processo já vive em namespaces"
nota "Cada link é um namespace; o número entre [] é o inode que o identifica."
nota "Dois processos com o mesmo inode estão no mesmo namespace."
run 'ls -l /proc/self/ns | awk "NR>1 {print \$9, \$11}"'

titulo "2. PID namespace: o processo vira PID 1"
nota "--fork: o filho entra no namespace novo. --mount-proc: remonta /proc, senão o ps"
nota "continuaria lendo o /proc antigo e mostraria todos os processos."
run 'unshare --pid --fork --mount-proc ps -o pid,ppid,cmd'
nota "Visto de fora, o mesmo processo tem um PID normal. PID 1 também é o 'init' do"
nota "namespace: se ele morre, o kernel mata todo mundo lá dentro (por isso existe tini/dumb-init)."
run 'unshare --pid --fork --mount-proc sleep 30 & sleep 0.5; ps -o pid,cmd -C sleep; kill %1 2>/dev/null; wait 2>/dev/null; true'

titulo "3. UTS namespace: hostname próprio"
run 'unshare --uts bash -c "hostname dentro-do-ns; echo dentro: \$(hostname)"; echo fora: $(hostname)'

titulo "4. Mount namespace: montagens invisíveis para fora"
run 'unshare --mount bash -c "mount -t tmpfs tmpfs /mnt && touch /mnt/segredo && ls /mnt"; echo "fora, /mnt tem: [$(ls /mnt)]"'

titulo "5. Network namespace: pilha de rede vazia"
nota "Sem eth0, sem rotas, lo em DOWN. As interfaces tunl0/gre0/etc. são placeholders"
nota "que o kernel cria em todo netns novo — estão DOWN e não levam a lugar nenhum."
run 'unshare --net cat /proc/net/dev | awk "NR>2 {print \$1}" | tr "\n" " "; echo'
run 'unshare --net cat /proc/net/route | wc -l | xargs echo "rotas no netns novo:"'
nota "O Docker liga esse netns ao host com um par veth + bridge docker0 + NAT (iptables)."

titulo "6. IPC namespace: filas/memória compartilhada System V separadas"
run 'ipcmk -Q >/dev/null; echo "fora: $(ipcs -q | grep -c 0x) filas"; unshare --ipc bash -c "echo dentro: \$(ipcs -q | grep -c 0x) filas"'

titulo "7. User namespace: root de mentira"
nota "Um usuário comum (nobody) cria um user ns e vira uid 0 LÁ DENTRO."
nota "uid_map '0 65534 1' = uid 0 dentro corresponde ao 65534 fora. Fora, continua sem poder nada."
run 'setpriv --reuid=65534 --regid=65534 --clear-groups bash -c "id; unshare --user --map-root-user bash -c \"id; cat /proc/self/uid_map; touch /etc/teste\"" 2>&1'
nota "É a base do Docker rootless e do Podman: root no container != root no host."

titulo "8. Entrando no namespace de outro processo (é o que docker exec faz)"
run 'unshare --uts --pid --fork --mount-proc bash -c "hostname alvo; sleep 30" & sleep 0.5
alvo=$(pgrep -n sleep)
echo "PID do alvo visto de fora: $alvo"
nsenter --target $alvo --uts --pid --mount hostname
nsenter --target $alvo --uts --pid --mount ps -o pid,cmd
kill $alvo'
