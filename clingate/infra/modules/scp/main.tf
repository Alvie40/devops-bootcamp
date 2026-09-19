locals {
  # Services that are global or have no regional endpoint. NotAction below exempts them from
  # the region restriction; without this list the SCP would break IAM, STS, Route 53, billing...
  # TO VERIFY against the current AWS "global services" list before relying on it.
  global_service_actions = [
    "account:*", "budgets:*", "ce:*", "cloudfront:*", "cur:*", "health:*", "iam:*",
    "identitystore:*", "organizations:*", "pricing:*", "route53:*", "route53domains:*",
    "shield:*", "sso:*", "sts:*", "support:*", "trustedadvisor:*", "waf:*", "wafv2:*",
    "ec2:DescribeRegions", "s3:GetAccountPublicAccessBlock", "s3:ListAllMyBuckets",
  ]

  policy_documents = {
    "clingate-baseline-guardrails" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "DenyLeaveOrganization"
          Effect   = "Deny"
          Action   = ["organizations:LeaveOrganization"]
          Resource = "*"
        },
        {
          # Identity Center is the only door in: no IAM users, no long-lived keys.
          Sid    = "DenyIamUsersAndLongLivedCredentials"
          Effect = "Deny"
          Action = [
            "iam:CreateUser", "iam:CreateAccessKey", "iam:CreateLoginProfile",
            "iam:UpdateLoginProfile", "iam:AttachUserPolicy", "iam:PutUserPolicy",
            "iam:CreateServiceSpecificCredential",
          ]
          Resource = "*"
        },
        {
          Sid      = "DenyChangingS3AccountPublicAccessBlock"
          Effect   = "Deny"
          Action   = ["s3:PutAccountPublicAccessBlock"]
          Resource = "*"
          Condition = {
            ArnNotLike = { "aws:PrincipalArn" = var.break_glass_role_arns }
          }
        },
        {
          Sid       = "DenyUnencryptedRds"
          Effect    = "Deny"
          Action    = ["rds:CreateDBInstance", "rds:CreateDBCluster"]
          Resource  = "*"
          Condition = { Bool = { "rds:StorageEncrypted" = "false" } }
        },
        {
          Sid       = "DenyUnencryptedEbsVolumes"
          Effect    = "Deny"
          Action    = ["ec2:CreateVolume"]
          Resource  = "*"
          Condition = { Bool = { "ec2:Encrypted" = "false" } }
        },
      ]
    })

    "clingate-protect-security-services" = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Sid    = "DenyTamperingWithDetectiveControls"
        Effect = "Deny"
        Action = [
          "cloudtrail:StopLogging", "cloudtrail:DeleteTrail", "cloudtrail:UpdateTrail",
          "cloudtrail:PutEventSelectors",
          "guardduty:DeleteDetector", "guardduty:DisassociateFromAdministratorAccount",
          "guardduty:DisassociateFromMasterAccount",
          "access-analyzer:DeleteAnalyzer",
          "config:StopConfigurationRecorder", "config:DeleteConfigurationRecorder",
          "config:DeleteDeliveryChannel",
        ]
        Resource = "*"
      }]
    })

    "clingate-restrict-regions" = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Sid       = "DenyOutsideAllowedRegions"
        Effect    = "Deny"
        NotAction = local.global_service_actions
        Resource  = "*"
        Condition = { StringNotEquals = { "aws:RequestedRegion" = var.allowed_regions } }
      }]
    })

    # Security OU only: the audit archive is write-once. Break-glass is the org access role;
    # its use is itself recorded by the organization trail.
    "clingate-protect-audit-archive" = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Sid    = "DenyWeakeningTheAuditArchive"
        Effect = "Deny"
        Action = [
          "s3:BypassGovernanceRetention", "s3:DeleteObjectVersion", "s3:DeleteBucket",
          "s3:PutBucketObjectLockConfiguration", "s3:PutBucketVersioning",
        ]
        Resource = "*"
        Condition = {
          ArnNotLike = { "aws:PrincipalArn" = ["arn:aws:iam::*:role/OrganizationAccountAccessRole"] }
        }
      }]
    })
  }

  root_policies = [
    "clingate-baseline-guardrails",
    "clingate-protect-security-services",
    "clingate-restrict-regions",
  ]
  security_ou_policies = ["clingate-protect-audit-archive"]
}

resource "aws_organizations_policy" "this" {
  for_each    = local.policy_documents
  name        = each.key
  description = "ClinGate guardrail: ${each.key}"
  type        = "SERVICE_CONTROL_POLICY"
  content     = each.value
}

resource "aws_organizations_policy_attachment" "root" {
  for_each  = toset(local.root_policies)
  policy_id = aws_organizations_policy.this[each.key].id
  target_id = var.root_id
}

resource "aws_organizations_policy_attachment" "security_ou" {
  for_each  = toset(local.security_ou_policies)
  policy_id = aws_organizations_policy.this[each.key].id
  target_id = var.security_ou_id
}
