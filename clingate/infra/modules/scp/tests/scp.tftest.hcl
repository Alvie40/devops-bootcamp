mock_provider "aws" {}

variables {
  root_id         = "r-ab12"
  security_ou_id  = "ou-ab12-cd34ef56"
  allowed_regions = ["us-east-1", "us-east-2"]
}

run "every_scp_fits_the_5120_character_limit" {
  command = plan
  assert {
    condition     = alltrue([for name, doc in output.policy_documents : length(doc) <= 5120])
    error_message = "an SCP exceeds the 5,120 character AWS limit"
  }
}

run "no_more_than_four_custom_scps_on_root_leaves_room_for_FullAWSAccess" {
  command = plan
  assert {
    condition     = length(aws_organizations_policy_attachment.root) <= 4
    error_message = "a target can have at most 5 SCPs including FullAWSAccess"
  }
}

run "org_membership_and_iam_users_are_denied" {
  command = plan
  assert {
    condition = contains(
      jsondecode(output.policy_documents["clingate-baseline-guardrails"]).Statement[0].Action,
      "organizations:LeaveOrganization"
    )
    error_message = "LeaveOrganization must be denied"
  }
  assert {
    condition = contains(
      jsondecode(output.policy_documents["clingate-baseline-guardrails"]).Statement[1].Action,
      "iam:CreateAccessKey"
    )
    error_message = "long-lived access keys must be denied"
  }
}

run "region_allow_list_is_exactly_the_variable_and_exempts_global_services" {
  command = plan
  assert {
    condition     = jsondecode(output.policy_documents["clingate-restrict-regions"]).Statement[0].Condition.StringNotEquals["aws:RequestedRegion"] == ["us-east-1", "us-east-2"]
    error_message = "region allow list must equal var.allowed_regions"
  }
  assert {
    condition     = contains(jsondecode(output.policy_documents["clingate-restrict-regions"]).Statement[0].NotAction, "iam:*")
    error_message = "IAM is global and must be exempt from the region deny"
  }
}

run "detective_controls_cannot_be_switched_off" {
  command = plan
  assert {
    condition = alltrue([
      for a in ["cloudtrail:StopLogging", "cloudtrail:DeleteTrail", "guardduty:DeleteDetector", "access-analyzer:DeleteAnalyzer"] :
      contains(jsondecode(output.policy_documents["clingate-protect-security-services"]).Statement[0].Action, a)
    ])
    error_message = "missing a tamper-prevention action"
  }
}

run "audit_archive_protection_attaches_to_the_security_ou_only" {
  command = plan
  assert {
    condition     = keys(aws_organizations_policy_attachment.security_ou) == ["clingate-protect-audit-archive"]
    error_message = "archive protection must attach to the security OU"
  }
}

run "empty_region_list_is_rejected" {
  command = plan
  variables {
    allowed_regions = []
  }
  expect_failures = [var.allowed_regions]
}
