mock_provider "aws" {}

variables {
  role_name        = "gh-clingate-prod"
  allowed_subjects = ["repo:Alvie40/devops-bootcamp:environment:prod"]
}

run "trust_is_pinned_to_audience_and_exact_subject" {
  command = plan
  assert {
    condition     = output.trust_conditions.StringEquals["token.actions.githubusercontent.com:aud"] == "sts.amazonaws.com"
    error_message = "audience must be sts.amazonaws.com"
  }
  assert {
    condition     = output.trust_conditions.StringEquals["token.actions.githubusercontent.com:sub"] == tolist(["repo:Alvie40/devops-bootcamp:environment:prod"])
    error_message = "subject must be the exact environment claim"
  }
}

run "wildcard_subject_is_rejected" {
  command = plan
  variables {
    allowed_subjects = ["repo:Alvie40/*:environment:prod"]
  }
  expect_failures = [var.allowed_subjects]
}

run "non_repo_subject_is_rejected" {
  command = plan
  variables {
    allowed_subjects = ["environment:prod"]
  }
  expect_failures = [var.allowed_subjects]
}

run "empty_subjects_are_rejected" {
  command = plan
  variables {
    allowed_subjects = []
  }
  expect_failures = [var.allowed_subjects]
}

run "provider_is_created_only_when_asked" {
  command = plan
  variables {
    create_provider = false
    provider_arn    = "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com"
  }
  assert {
    condition     = length(aws_iam_openid_connect_provider.github) == 0
    error_message = "no provider should be created"
  }
}
