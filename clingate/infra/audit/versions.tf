terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Configured at init time (see ../backend.hcl.example); nothing account-specific in git.
  backend "s3" {}
}
