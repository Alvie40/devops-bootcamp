variable "bucket_name" {
  type = string
}

variable "account_id" {
  description = "The security-tooling account id (owner of the bucket and the key)."
  type        = string
}

variable "management_account_id" {
  description = "Account that owns the organization trail."
  type        = string
}

variable "organization_id" {
  description = "o-xxxxxxxxxx: organization trails deliver under AWSLogs/<org id>/."
  type        = string
}

variable "trail_name" {
  type    = string
  default = "clingate-org-trail"
}

variable "trail_home_region" {
  type    = string
  default = "us-east-1"
}

variable "object_lock_days" {
  description = "Default GOVERNANCE retention. Short in the lab so teardown stays possible; compliance-mode and a policy-driven period for a prod shape."
  type        = number
  default     = 7
}

variable "expire_days" {
  description = "Delete current versions after this many days (cost control in the lab)."
  type        = number
  default     = 365
}

variable "tags" {
  type    = map(string)
  default = {}
}
