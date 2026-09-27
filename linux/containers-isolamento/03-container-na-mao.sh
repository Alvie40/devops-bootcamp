#!/usr/bin/env bash
# Um "container" sem Docker: namespaces + rootfs + cgroup. É tudo que o runc faz
# no essencial (o resto é capabilities, seccomp, LSM e rede — ver 05).
source "$(dirname "$0")/_lib.sh"

ROOTFS=/tmp/rootfs
CG=/sys/fs/cgroup/meu-container
trap 'rmdir $CG 2>/dev/null' EXIT

titulo "1. Imagem = um tar de filesystem"
nota "Gerado pelo lab.sh com 'docker export' de um container alpine."
run "mkdir -p $ROOTFS && tar -xf /lab/rootfs/alpine.tar -C $ROOTFS && ls $ROOTFS"
run "cat $ROOTFS/etc/os-release | head -2"

titulo "2. cgroup com limites"
run "mkdir -p $CG && echo 64M > $CG/memory.max && echo 0 > $CG/memory.swap.max && echo 10 > $CG/pids.max && echo '50000 100000' > $CG/cpu.max"

titulo "3. Juntando tudo"
nota "O shell entra no cgroup e depois dá unshare (o filho herda o cgroup)."
nota "--root faz chroot no rootfs; --mount-proc monta um /proc novo lá dentro."
nota "/init.sh é o 'CMD' do nosso container: o que roda como PID 1 lá dentro."
cat > $ROOTFS/init.sh <<'EOF'
#!/bin/sh
hostname meu-container
echo "hostname:   $(hostname)"
echo "distro:     $(grep PRETTY /etc/os-release | cut -d= -f2)"
echo "kernel:     $(uname -r)   <- o MESMO do host"
echo "cgroup:     $(cat /proc/self/cgroup)   <- cgroup ns: se vê como raiz"
mkdir -p /sys/fs/cgroup && mount -t cgroup2 none /sys/fs/cgroup
echo "mem limite: $(cat /sys/fs/cgroup/memory.max) bytes   <- o cgroup 'raiz' dele é o meu-container"
echo "processos:"; ps
echo "interfaces: $(ip -o link | awk -F': ' '{print $2}' | grep -v NONE)"
EOF
chmod +x $ROOTFS/init.sh
run "cat $ROOTFS/init.sh"
run "bash -c 'echo \$\$ > $CG/cgroup.procs; exec unshare --pid --fork --mount --uts --ipc --net --cgroup --root=$ROOTFS --mount-proc /init.sh'"
nota "Só lo (e DOWN): sem eth0, sem rota. O grep esconde os placeholders tunl0/gre0/... do netns novo."

titulo "O que falta para ser um container 'de verdade'"
nota "pivot_root em vez de chroot (chroot tem fuga conhecida para quem é root)."
nota "Rede: veth + bridge + NAT. Capabilities reduzidas. Filtro seccomp. AppArmor/SELinux."
nota "Overlayfs para camadas de imagem copy-on-write. Isso é o runc + containerd."
