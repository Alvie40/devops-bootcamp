terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # Deliberately NO backend: this stack creates the bucket every other stack stores state in.
  # It runs once with local state; the tiny state file is then kept in the bucket it created
  # (terraform init -migrate-state after adding a backend block) or simply archived.
}
