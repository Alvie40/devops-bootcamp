# Helpers compartilhados pelos exercícios. Não execute direto: `source _lib.sh`.

if [ ! -e /.dockerenv ] || [ ! -w /sys/fs/cgroup ]; then
  echo "Rode dentro do lab: ./lab.sh  (container --privileged --cgroupns=host)" >&2
  exit 1
fi

bold=$'\e[1m'; dim=$'\e[2m'; cyan=$'\e[36m'; reset=$'\e[0m'

# titulo "texto": cabeçalho de seção
titulo() { printf '\n%s== %s ==%s\n' "$bold" "$1" "$reset"; }

# nota "texto": explicação curta antes do comando
nota() { printf '%s# %s%s\n' "$dim" "$1" "$reset"; }

# run 'comando': mostra o comando e executa. PAUSE=1 espera Enter antes de cada um.
run() {
  printf '%s$ %s%s\n' "$cyan" "$1" "$reset"
  if [ "${PAUSE:-0}" = 1 ]; then read -r -p "  [enter] " _; fi
  bash -c "$1"
  echo
}
