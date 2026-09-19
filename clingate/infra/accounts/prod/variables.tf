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

variable "github_repo" {
  description = "OWNER/REPO whose workflows may assume the deploy role."
  type        = string
  default     = "Alvie40/devops-bootcamp"
}
