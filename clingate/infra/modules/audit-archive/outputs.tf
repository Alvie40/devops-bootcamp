output "bucket_name" {
  value = aws_s3_bucket.archive.id
}

output "kms_key_arn" {
  value = aws_kms_key.archive.arn
}

output "bucket_policy" {
  value = local.bucket_policy
}

output "key_policy" {
  value = local.key_policy
}
