# GitHub Actions -> AWS with no stored credentials: the workflow presents a short-lived OIDC
# token and STS exchanges it for a session. Trust is pinned to exact `sub` values.
resource "aws_iam_openid_connect_provider" "github" {
  count          = var.create_provider ? 1 : 0
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  tags           = var.tags
}

locals {
  provider_arn = var.create_provider ? aws_iam_openid_connect_provider.github[0].arn : var.provider_arn

  # Known at plan time, so it can be asserted on offline.
  trust_conditions = {
    StringEquals = {
      "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
      "token.actions.githubusercontent.com:sub" = var.allowed_subjects
    }
  }
}

resource "aws_iam_role" "this" {
  name                 = var.role_name
  max_session_duration = var.max_session_duration
  permissions_boundary = var.permissions_boundary_arn
  tags                 = var.tags

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = local.provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = local.trust_conditions
    }]
  })
}

resource "aws_iam_role_policy_attachment" "managed" {
  for_each   = toset(var.managed_policy_arns)
  role       = aws_iam_role.this.name
  policy_arn = each.value
}
