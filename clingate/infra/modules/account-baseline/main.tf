# Account-level defaults every member account gets. The SCP forbids changing the S3 block
# outside the org access role, so this is the only place it is set.
resource "aws_s3_account_public_access_block" "this" {
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_ebs_encryption_by_default" "this" {
  enabled = true
}
