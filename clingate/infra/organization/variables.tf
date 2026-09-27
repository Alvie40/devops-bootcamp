variable "region" {
  description = "Home region: Organizations, Identity Center and the org trail live here."
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "SSO profile for the MANAGEMENT account (aws sso login). Never a static-key profile."
  type        = string
  default     = null
}

variable "account_emails" {
  description = "Root e-mail of each member account. Must be unique per account, reachable for the life of the account, and protected by MFA on the mailbox (it is the password-reset path to every root)."
  type        = map(string)

  validation {
    condition     = alltrue([for k in ["security-tooling", "staging", "prod"] : contains(keys(var.account_emails), k)])
    error_message = "account_emails needs exactly the keys security-tooling, staging and prod."
  }

  validation {
    condition     = length(distinct([for e in values(var.account_emails) : lower(e)])) == length(var.account_emails)
    error_message = "Each account needs a distinct root e-mail."
  }
}

variable "allowed_regions" {
  type    = list(string)
  default = ["us-east-1"]
}

variable "alert_emails" {
  description = "Budget and cost-anomaly recipients."
  type        = list(string)
}

variable "org_monthly_budget_usd" {
  type    = number
  default = 25
}

variable "staging_monthly_budget_usd" {
  type    = number
  default = 20
}

variable "prod_monthly_budget_usd" {
  type    = number
  default = 10
}

variable "admin_user" {
  description = "The one human in Identity Center. MFA is enforced in the Identity Center console (no Terraform resource for it)."
  type = object({
    user_name   = string
    given_name  = string
    family_name = string
    email       = string
  })
}
