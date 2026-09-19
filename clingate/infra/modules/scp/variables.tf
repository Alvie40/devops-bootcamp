variable "root_id" {
  description = "Organization root id (r-xxxx). Guardrails attach here and apply to every member account."
  type        = string
}

variable "security_ou_id" {
  description = "OU that holds the security-tooling account (audit archive protections attach here)."
  type        = string
}

variable "allowed_regions" {
  description = "Regions in which regional services may be used."
  type        = list(string)
  default     = ["us-east-1"]

  validation {
    condition     = length(var.allowed_regions) > 0
    error_message = "allowed_regions must not be empty (that would deny every regional service)."
  }
}

variable "break_glass_role_arns" {
  description = "Principals exempt from the protective (tamper-prevention) statements. Terraform runs through OrganizationAccountAccessRole; CI roles are listed explicitly."
  type        = list(string)
  default = [
    "arn:aws:iam::*:role/OrganizationAccountAccessRole",
    "arn:aws:iam::*:role/gh-clingate-*",
  ]
}
