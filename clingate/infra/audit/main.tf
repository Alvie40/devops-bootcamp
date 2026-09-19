provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = { Project = "clingate", ManagedBy = "terraform", Stack = "audit" }
  }
}

# Organization trail: every account's management events, delivered to the archive in the
# security-tooling account. First copy of management events is free (verify current pricing).
resource "aws_cloudtrail" "organization" {
  name                          = var.trail_name
  s3_bucket_name                = var.audit_bucket_name
  kms_key_id                    = var.audit_kms_key_arn
  is_organization_trail         = true
  is_multi_region_trail         = true
  include_global_service_events = true
  enable_log_file_validation    = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }
}
