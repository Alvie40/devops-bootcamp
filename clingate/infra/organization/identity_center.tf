# Prerequisite (manual, once): enable IAM Identity Center with the organization instance in the
# console. There is no Terraform resource for that step, and MFA enforcement is also console-only.
data "aws_ssoadmin_instances" "this" {}

locals {
  sso_arn  = tolist(data.aws_ssoadmin_instances.this.arns)[0]
  store_id = tolist(data.aws_ssoadmin_instances.this.identity_store_ids)[0]

  permission_sets = {
    orgadmin = {
      name     = "ClinGateOrgAdmin"
      duration = "PT1H"
      policies = ["arn:aws:iam::aws:policy/AdministratorAccess"]
    }
    operator = {
      name     = "ClinGateOperator"
      duration = "PT4H"
      # Day-to-day operation. No IAM/Organizations write: infrastructure changes go through the pipeline.
      policies = ["arn:aws:iam::aws:policy/PowerUserAccess"]
    }
    auditor = {
      name     = "ClinGateSecurityAuditor"
      duration = "PT8H"
      policies = ["arn:aws:iam::aws:policy/SecurityAudit", "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"]
    }
  }

  management_id = data.aws_caller_identity.current.account_id
  account_ids   = { for k, a in aws_organizations_account.this : k => a.id }

  assignments = {
    "orgadmin/management"      = { group = "orgadmin", account = local.management_id }
    "operator/staging"         = { group = "operator", account = local.account_ids["staging"] }
    "operator/prod"            = { group = "operator", account = local.account_ids["prod"] }
    "auditor/management"       = { group = "auditor", account = local.management_id }
    "auditor/security-tooling" = { group = "auditor", account = local.account_ids["security-tooling"] }
    "auditor/staging"          = { group = "auditor", account = local.account_ids["staging"] }
    "auditor/prod"             = { group = "auditor", account = local.account_ids["prod"] }
  }

  managed_policy_pairs = merge([
    for key, ps in local.permission_sets : {
      for arn in ps.policies : "${key}/${arn}" => { permission_set = key, policy_arn = arn }
    }
  ]...)
}

resource "aws_ssoadmin_permission_set" "this" {
  for_each         = local.permission_sets
  name             = each.value.name
  instance_arn     = local.sso_arn
  session_duration = each.value.duration
}

resource "aws_ssoadmin_managed_policy_attachment" "this" {
  for_each           = local.managed_policy_pairs
  instance_arn       = local.sso_arn
  permission_set_arn = aws_ssoadmin_permission_set.this[each.value.permission_set].arn
  managed_policy_arn = each.value.policy_arn
}

resource "aws_identitystore_group" "this" {
  for_each          = local.permission_sets
  identity_store_id = local.store_id
  display_name      = "clingate-${each.key}"
}

resource "aws_identitystore_user" "admin" {
  identity_store_id = local.store_id
  user_name         = var.admin_user.user_name
  display_name      = "${var.admin_user.given_name} ${var.admin_user.family_name}"

  name {
    given_name  = var.admin_user.given_name
    family_name = var.admin_user.family_name
  }

  emails {
    value   = var.admin_user.email
    primary = true
  }
}

resource "aws_identitystore_group_membership" "admin" {
  for_each          = local.permission_sets
  identity_store_id = local.store_id
  group_id          = aws_identitystore_group.this[each.key].group_id
  member_id         = aws_identitystore_user.admin.user_id
}

resource "aws_ssoadmin_account_assignment" "this" {
  for_each           = local.assignments
  instance_arn       = local.sso_arn
  permission_set_arn = aws_ssoadmin_permission_set.this[each.value.group].arn
  principal_id       = aws_identitystore_group.this[each.value.group].group_id
  principal_type     = "GROUP"
  target_id          = each.value.account
  target_type        = "AWS_ACCOUNT"
}
