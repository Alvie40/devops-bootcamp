output "organization_id" {
  value = aws_organizations_organization.this.id
}

output "management_account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "account_ids" {
  description = "Feed these to accounts/* as var.account_id."
  value       = { for k, a in aws_organizations_account.this : k => a.id }
}

output "permission_set_arns" {
  value = { for k, p in aws_ssoadmin_permission_set.this : k => p.arn }
}
