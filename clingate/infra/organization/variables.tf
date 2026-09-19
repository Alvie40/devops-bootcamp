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

variable "account_email_template" {
  description = "Each member account needs a unique root e-mail. `%s` is replaced by the account key. Plus-addressing works: you+clingate-%s@example.com."
  type        = string

  validation {
    condition     = strcontains(var.account_email_template, "%s")
    error_message = "account_email_template must contain %s."
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
