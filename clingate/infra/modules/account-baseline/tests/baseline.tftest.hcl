mock_provider "aws" {}

run "public_access_blocked_and_ebs_encrypted_by_default" {
  command = plan
  assert {
    condition     = aws_s3_account_public_access_block.this.block_public_acls && aws_s3_account_public_access_block.this.block_public_policy && aws_s3_account_public_access_block.this.ignore_public_acls && aws_s3_account_public_access_block.this.restrict_public_buckets
    error_message = "all four S3 public-access blocks must be on"
  }
  assert {
    condition     = aws_ebs_encryption_by_default.this.enabled
    error_message = "EBS encryption by default must be on"
  }
}
