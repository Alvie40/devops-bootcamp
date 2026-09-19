variable "role_name" {
  type = string
}

variable "create_provider" {
  description = "Create the account's GitHub OIDC provider. Exactly one module call per account sets this true."
  type        = bool
  default     = true
}

variable "provider_arn" {
  description = "Existing provider ARN when create_provider = false."
  type        = string
  default     = null
}

variable "allowed_subjects" {
  description = "Exact OIDC `sub` claims allowed to assume the role, e.g. repo:OWNER/REPO:environment:prod. No wildcards."
  type        = list(string)

  validation {
    condition     = length(var.allowed_subjects) > 0 && alltrue([for s in var.allowed_subjects : startswith(s, "repo:") && !strcontains(s, "*")])
    error_message = "allowed_subjects must be non-empty, start with 'repo:' and contain no wildcards."
  }
}

variable "managed_policy_arns" {
  type    = list(string)
  default = []
}

variable "permissions_boundary_arn" {
  type    = string
  default = null
}

variable "max_session_duration" {
  type    = number
  default = 3600
}

variable "tags" {
  type    = map(string)
  default = {}
}
