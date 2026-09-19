output "policy_documents" {
  description = "SCP name => JSON document (also what the offline tests assert on)."
  value       = local.policy_documents
}

output "policy_ids" {
  value = { for k, p in aws_organizations_policy.this : k => p.id }
}
