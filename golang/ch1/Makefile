.DEFAULT_GOAL := build

.PHONY: fmt fmt-check vet lint build test run clean

# Formata o pacote (reescreve os arquivos). Primeiro elo da cadeia local.
fmt:
	go fmt ./...

# Variante pra CI: falha se algo estiver desformatado, sem reescrever nada.
fmt-check:
	@test -z "$$(gofmt -l .)" || { echo "arquivos nao formatados:"; gofmt -l .; exit 1; }

vet: fmt
	go vet ./...

# staticcheck substitui o golint do livro (arquivado em 2021).
# Pula quando nao esta instalado, em vez de quebrar o build.
lint: fmt
	@if command -v staticcheck >/dev/null; then \
		staticcheck ./...; \
	else \
		echo "staticcheck ausente (brew install staticcheck), pulando lint"; \
	fi

# "." em vez de hello.go: compila o pacote inteiro e nomeia o binario
# pelo modulo, entao um segundo arquivo no main nao quebra o build.
build: vet
	go build .

test: vet
	go test ./...

run: build
	./hello_world

clean:
	go clean
	rm -f hello_world
