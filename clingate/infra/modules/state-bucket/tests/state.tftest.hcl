mock_provider "aws" {}

variables {
  bucket_name = "clingate-tfstate-111122223333"
}

run "state_is_versioned_encrypted_private_and_tls_only" {
  command = plan
  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled"
    error_message = "state bucket must be versioned"
  }
  assert {
    condition     = aws_kms_key.state.enable_key_rotation
    error_message = "state key rotation must be on"
  }
  assert {
    condition     = one(one(aws_s3_bucket_server_side_encryption_configuration.this.rule).apply_server_side_encryption_by_default).sse_algorithm == "aws:kms"
    error_message = "state must be encrypted with a customer-managed KMS key"
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.this.block_public_acls && aws_s3_bucket_public_access_block.this.restrict_public_buckets
    error_message = "public access must be blocked"
  }
  assert {
    condition     = jsondecode(output.bucket_policy).Statement[0].Condition.Bool["aws:SecureTransport"] == "false"
    error_message = "must deny non-TLS requests"
  }
}
