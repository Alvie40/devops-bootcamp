provider "aws" {
  region  = var.region
  profile = var.aws_profile

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/OrganizationAccountAccessRole"
    session_name = "clingate-terraform-staging"
  }

  default_tags {
    tags = { Project = "clingate", ManagedBy = "terraform", Account = "staging" }
  }
}
