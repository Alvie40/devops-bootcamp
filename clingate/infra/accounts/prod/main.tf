module "baseline" {
  source = "../../modules/account-baseline"
}

# Prod trust is narrower than staging: only the GitHub Environment `prod`, which carries the
# required-reviewer rule. A push to main alone can never assume this role.
module "github_deploy" {
  source = "../../modules/github-oidc"

  role_name           = "gh-clingate-prod"
  allowed_subjects    = ["repo:${var.github_repo}:environment:prod"]
  managed_policy_arns = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
}
