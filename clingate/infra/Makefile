# Offline checks only: nothing here talks to AWS. `plan`/`apply` are deliberate, manual steps
# documented in README.md and need real accounts.
SHELL := /bin/bash
export TF_PLUGIN_CACHE_DIR := $(HOME)/.terraform.d/plugin-cache
STACKS  := bootstrap-state organization audit accounts/security-tooling accounts/staging accounts/prod
MODULES := modules/scp modules/github-oidc modules/state-bucket modules/audit-archive modules/account-baseline

.PHONY: all fmt fmt-check validate test scan lock
all: fmt-check validate test scan

fmt: ; terraform fmt -recursive .
fmt-check: ; terraform fmt -check -recursive .

validate: ## init (no backend) + validate every stack and module
	@mkdir -p $(TF_PLUGIN_CACHE_DIR)
	@set -e; for d in $(STACKS) $(MODULES); do \
	  echo "== validate $$d"; \
	  (cd $$d && terraform init -backend=false -input=false >/dev/null && terraform validate -no-color | grep -E "Success|Error" ); \
	done

test: ## offline unit tests (mock provider) for every module
	@set -e; for d in $(MODULES); do \
	  echo "== test $$d"; \
	  (cd $$d && terraform init -backend=false -input=false >/dev/null && terraform test -no-color | grep -E "^Success|^Failure|fail" ); \
	done

scan: ## IaC misconfiguration scan (HIGH/CRITICAL fails)
	trivy config --severity HIGH,CRITICAL --exit-code 1 --skip-dirs '**/.terraform' .

lock: ## record provider hashes for the platforms we use (commit the lock files)
	@for d in $(STACKS); do (cd $$d && terraform providers lock -platform=darwin_arm64 -platform=linux_amd64 >/dev/null); done
