output "role_arn" {
  value = aws_iam_role.this.arn
}

output "provider_arn" {
  value = local.provider_arn
}

output "trust_conditions" {
  description = "The audience/subject conditions of the trust policy."
  value       = local.trust_conditions
}
