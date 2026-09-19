provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = { Project = "clingate", ManagedBy = "terraform", Stack = "organization" }
  }
}

data "aws_caller_identity" "current" {}

# The organization is created once by hand (console), then imported:
#   terraform import aws_organizations_organization.this <o-id>
resource "aws_organizations_organization" "this" {
  feature_set          = "ALL"
  enabled_policy_types = ["SERVICE_CONTROL_POLICY"]
  aws_service_access_principals = [
    "access-analyzer.amazonaws.com",
    "cloudtrail.amazonaws.com",
    "sso.amazonaws.com",
  ]
}

locals {
  root_id = aws_organizations_organization.this.roots[0].id

  accounts = {
    security-tooling = { name = "clingate-security-tooling", ou = "security" }
    staging          = { name = "clingate-staging", ou = "workloads" }
    prod             = { name = "clingate-prod", ou = "workloads" }
  }
}

resource "aws_organizations_organizational_unit" "security" {
  name      = "Security"
  parent_id = local.root_id
}

resource "aws_organizations_organizational_unit" "workloads" {
  name      = "Workloads"
  parent_id = local.root_id
}

locals {
  ou_ids = {
    security  = aws_organizations_organizational_unit.security.id
    workloads = aws_organizations_organizational_unit.workloads.id
  }
}

# Creating an account is cheap and easy; closing one takes 90 days and is not reversible.
# prevent_destroy makes `terraform destroy` refuse instead of quietly closing accounts.
resource "aws_organizations_account" "this" {
  for_each = local.accounts

  name                       = each.value.name
  email                      = format(var.account_email_template, each.key)
  parent_id                  = local.ou_ids[each.value.ou]
  role_name                  = "OrganizationAccountAccessRole"
  iam_user_access_to_billing = "DENY"
  close_on_deletion          = false

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [role_name, iam_user_access_to_billing]
  }
}

module "scp" {
  source = "../modules/scp"

  root_id         = local.root_id
  security_ou_id  = local.ou_ids.security
  allowed_regions = var.allowed_regions
}

# IAM Access Analyzer (organization scope) runs from the security account, not from management.
resource "aws_organizations_delegated_administrator" "access_analyzer" {
  account_id        = aws_organizations_account.this["security-tooling"].id
  service_principal = "access-analyzer.amazonaws.com"
}
