output "audit_bucket_name" {
  value = module.audit_archive.bucket_name
}

output "audit_kms_key_arn" {
  value = module.audit_archive.kms_key_arn
}
