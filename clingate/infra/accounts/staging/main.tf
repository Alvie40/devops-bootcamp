module "baseline" {
  source = "../../modules/account-baseline"
}

# P2 gives the pipeline identity read-only access. Deploy permissions (with a permissions
# boundary) are enumerated in P3, once the resources they must create exist.
module "github_deploy" {
  source = "../../modules/github-oidc"

  role_name = "gh-clingate-staging"
  allowed_subjects = [
    "repo:${var.github_repo}:ref:refs/heads/main",
    "repo:${var.github_repo}:environment:staging",
  ]
  managed_policy_arns = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
}
