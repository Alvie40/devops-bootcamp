# ClinGate infrastructure (P2: accounts, identity, guardrails)

Terraform for the AWS foundation only: organization, accounts, guardrails (SCPs), Identity Center,
budgets, the audit archive, and the pipeline's OIDC identities. **No workload resources** (no VPC,
EKS, Aurora, NAT): those are P3. Idle cost of everything here is a few dollars a month, dominated by
the two KMS keys.

**Status:** written and verified **offline** (`make all`: fmt, validate, 17 module tests with a mocked
provider, Trivy config scan; the tests were mutation-checked). Nothing has been planned or applied
against AWS yet, so the P2 exit criteria ("`plan` clean, SSO login works") are **not met**.

## Decision needed before any `apply`

The machine's default AWS profile is a static-key IAM user (`cli-admin`) in an existing account.
That must **not** become the organization's management account: the design forbids long-lived keys,
and the management account should hold nothing but the organization. Create a **new** AWS account
for management (unique root e-mail, root MFA), and use it only through Identity Center.

## Layout

```
bootstrap-state/   creates the S3 + KMS bucket every other stack stores state in (local state, once)
organization/      management account: org, OUs, member accounts, SCPs, Identity Center, budgets
accounts/
  security-tooling/  audit archive (Object Lock, KMS), org Access Analyzer
  staging/  prod/    account baseline + GitHub OIDC deploy role (read-only until P3)
audit/             management account: the organization CloudTrail -> the archive
modules/           scp, github-oidc, state-bucket, audit-archive, account-baseline (+ tests)
```

## Manual steps (no Terraform resource exists for these)

1. New AWS account for management; root MFA on; no root access keys.
2. Console, Organizations: create the organization (all features).
3. Console, IAM Identity Center: enable with the organization instance; **enforce MFA** for users.
4. `aws configure sso` for the management account, then `aws sso login --profile <name>`.
5. After the member accounts exist: request Service Quota increases in `staging` (Fargate and EC2
   vCPU, EKS). Increases can take days; do this before P3, not during it.

## Apply order (each stack: `plan`, read it, then `apply`)

```bash
cd bootstrap-state && terraform init && terraform apply            # bucket + key
# then, for every other stack:
terraform init -backend-config=../backend.hcl -backend-config="key=<stack>/terraform.tfstate"

cd organization
terraform import aws_organizations_organization.this <o-id>        # created by hand in step 2
terraform apply                                                    # OUs, accounts, SCPs, SSO, budgets
terraform output account_ids

cd accounts/security-tooling   # -var account_id=... management_account_id=... organization_id=...
terraform apply                                                    # audit archive + analyzer
cd audit                       # -var audit_bucket_name=... audit_kms_key_arn=...
terraform apply                                                    # org trail
cd accounts/staging && terraform apply
cd accounts/prod    && terraform apply
```

Member-account stacks run through `OrganizationAccountAccessRole` (the SCPs exempt it). Accounts are
`prevent_destroy`: closing an account takes 90 days and cannot be undone.

## Offline checks

```bash
make all      # fmt-check, validate (all stacks + modules), test (all modules), scan (Trivy)
make lock     # record provider hashes for darwin_arm64 and linux_amd64
```

## Things to verify before relying on them

SCP global-services list and the `rds:StorageEncrypted` / `ec2:Encrypted` condition keys ·
whether IAM supports pinning more GitHub OIDC claims (e.g. the workflow ref) · Budgets and Cost
Anomaly Detection pricing (the third budget may not be free) · that the first organization trail is
free · AWS provider v6 attribute names against a real `plan` · Identity Center permission-set
session limits.
