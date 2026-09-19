module "baseline" {
  source = "../../modules/account-baseline"
}

module "audit_archive" {
  source = "../../modules/audit-archive"

  bucket_name           = "clingate-audit-archive-${var.account_id}"
  account_id            = var.account_id
  management_account_id = var.management_account_id
  organization_id       = var.organization_id
  trail_name            = var.trail_name
  trail_home_region     = var.region
}

# Needs the delegated-administrator registration done in ../../organization.
resource "aws_accessanalyzer_analyzer" "organization" {
  analyzer_name = "clingate-org-external-access"
  type          = "ORGANIZATION"
}
