# Budgets and anomaly detection are ALARMS, not brakes: billing data lags by hours. The real
# cost controls are scale ceilings, time-boxed runs and the nightly destroy (SPEC 8.3).
locals {
  thresholds = [
    { pct = 50, type = "ACTUAL" },
    { pct = 80, type = "ACTUAL" },
    { pct = 100, type = "FORECASTED" },
  ]

  scoped_budgets = {
    staging = var.staging_monthly_budget_usd
    prod    = var.prod_monthly_budget_usd
  }
}

resource "aws_budgets_budget" "organization" {
  name         = "clingate-org-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.org_monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = local.thresholds
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value.pct
      threshold_type             = "PERCENTAGE"
      notification_type          = notification.value.type
      subscriber_email_addresses = var.alert_emails
    }
  }
}

resource "aws_budgets_budget" "account" {
  for_each = local.scoped_budgets

  name         = "clingate-${each.key}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(each.value)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "LinkedAccount"
    values = [aws_organizations_account.this[each.key].id]
  }

  dynamic "notification" {
    for_each = local.thresholds
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value.pct
      threshold_type             = "PERCENTAGE"
      notification_type          = notification.value.type
      subscriber_email_addresses = var.alert_emails
    }
  }
}

resource "aws_ce_anomaly_monitor" "services" {
  name              = "clingate-services"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "email" {
  name             = "clingate-anomalies"
  frequency        = "DAILY"
  monitor_arn_list = [aws_ce_anomaly_monitor.services.arn]

  dynamic "subscriber" {
    for_each = toset(var.alert_emails)
    content {
      type    = "EMAIL"
      address = subscriber.value
    }
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      match_options = ["GREATER_THAN_OR_EQUAL"]
      values        = ["5"]
    }
  }
}
