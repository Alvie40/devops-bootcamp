variable "region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  description = "SSO profile for the MANAGEMENT account; the stack then assumes OrganizationAccountAccessRole in the target."
  type        = string
  default     = null
}

variable "account_id" {
  description = "From `terraform output account_ids` in ../../organization."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "account_id must be 12 digits."
  }
}

variable "management_account_id" {
  type = string
}

variable "organization_id" {
  type = string
}

variable "trail_name" {
  type    = string
  default = "clingate-org-trail"
}
