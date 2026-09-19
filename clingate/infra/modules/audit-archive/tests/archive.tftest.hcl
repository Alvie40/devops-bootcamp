mock_provider "aws" {}

variables {
  bucket_name           = "clingate-audit-archive-111122223333"
  account_id            = "111122223333"
  management_account_id = "444455556666"
  organization_id       = "o-ab12cd34ef"
}

run "archive_is_write_once_encrypted_and_private" {
  command = plan
  assert {
    condition     = aws_s3_bucket.archive.object_lock_enabled
    error_message = "Object Lock must be enabled"
  }
  assert {
    condition     = one(one(aws_s3_bucket_object_lock_configuration.archive.rule).default_retention).mode == "GOVERNANCE"
    error_message = "lab uses GOVERNANCE so teardown stays possible"
  }
  assert {
    condition     = aws_kms_key.archive.enable_key_rotation
    error_message = "key rotation must be on"
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.archive.block_public_policy && aws_s3_bucket_public_access_block.archive.restrict_public_buckets
    error_message = "public access must be blocked"
  }
}

run "bucket_policy_denies_plain_http_and_scopes_cloudtrail_to_our_trail" {
  command = plan
  assert {
    condition     = jsondecode(output.bucket_policy).Statement[0].Condition.Bool["aws:SecureTransport"] == "false"
    error_message = "non-TLS must be denied"
  }
  assert {
    condition     = jsondecode(output.bucket_policy).Statement[2].Condition.StringEquals["aws:SourceArn"] == "arn:aws:cloudtrail:us-east-1:444455556666:trail/clingate-org-trail"
    error_message = "CloudTrail writes must be tied to the organization trail ARN (confused-deputy protection)"
  }
  assert {
    condition = toset(jsondecode(output.bucket_policy).Statement[2].Resource) == toset([
      "arn:aws:s3:::clingate-audit-archive-111122223333/AWSLogs/444455556666/*",
      "arn:aws:s3:::clingate-audit-archive-111122223333/AWSLogs/o-ab12cd34ef/*",
    ])
    error_message = "CloudTrail may only write under the management account and organization prefixes"
  }
}

run "key_policy_lets_cloudtrail_encrypt_only_for_the_management_accounts_trails" {
  command = plan
  assert {
    condition     = jsondecode(output.key_policy).Statement[1].Condition.StringLike["kms:EncryptionContext:aws:cloudtrail:arn"] == "arn:aws:cloudtrail:*:444455556666:trail/*"
    error_message = "encryption context must be pinned to the management account"
  }
}
