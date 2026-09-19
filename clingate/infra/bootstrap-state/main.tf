variable "region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  type    = string
  default = null
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = { Project = "clingate", ManagedBy = "terraform", Stack = "bootstrap-state" }
  }
}

data "aws_caller_identity" "current" {}

module "state" {
  source      = "../modules/state-bucket"
  bucket_name = "clingate-tfstate-${data.aws_caller_identity.current.account_id}"
}

output "state_bucket" {
  value = module.state.bucket_name
}

output "state_kms_key_arn" {
  value = module.state.kms_key_arn
}
