#!/usr/bin/env bash
# Sobe a "máquina Linux" do lab: um container Ubuntu privilegiado que enxerga a
# hierarquia de cgroup real da VM do Docker Desktop. É ali que os exercícios rodam.
#
#   ./lab.sh            -> shell interativo no lab
#   ./lab.sh 02-cgroups.sh -> roda um exercício e sai
#
# ATENÇÃO: --privileged + --cgroupns=host dá ao container poder sobre o kernel da VM.
# Só aceitável porque a VM é descartável. Nunca faça isso em produção (ver 05).
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p rootfs
if [ ! -f rootfs/alpine.tar ]; then
  echo "Gerando rootfs do Alpine (usado no 03)..."
  cid=$(docker create alpine:3.20)
  docker export "$cid" > rootfs/alpine.tar
  docker rm "$cid" >/dev/null
fi

tty_flag=(); [ -t 0 ] && tty_flag=(-it)
cmd=(bash); [ $# -gt 0 ] && cmd=(bash "$@")

exec docker run --rm "${tty_flag[@]}" \
  --privileged --cgroupns=host \
  --hostname lab \
  -v "$PWD":/lab -w /lab \
  ubuntu:24.04 "${cmd[@]}"
