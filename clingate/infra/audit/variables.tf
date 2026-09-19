variable "region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  type    = string
  default = null
}

variable "trail_name" {
  description = "Must match the trail name baked into the archive's bucket and key policies."
  type        = string
  default     = "clingate-org-trail"
}

variable "audit_bucket_name" {
  description = "Output of accounts/security-tooling."
  type        = string
}

variable "audit_kms_key_arn" {
  description = "Output of accounts/security-tooling."
  type        = string
}
