output "bucket_name" {
  value = aws_s3_bucket.this.id
}

output "bucket_policy" {
  value = local.tls_only_policy
}

output "kms_key_arn" {
  description = "Set as `kms_key_id` in backend configs so state writes use this key explicitly."
  value       = aws_kms_key.state.arn
}
