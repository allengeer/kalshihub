# Terraform Infrastructure

This directory contains Terraform configurations for deploying and managing Kalshihub's Google Cloud Platform infrastructure.

## Overview

The Terraform configuration deploys:
- **Google Cloud Storage Bucket**: For application data storage with versioning and lifecycle management

## Prerequisites

1. **Google Cloud Project**: Active GCP project with billing enabled
2. **Service Account**: Service account with the following roles:
   - `roles/storage.admin` - For managing Cloud Storage buckets
   - `roles/iam.serviceAccountAdmin` - For managing IAM bindings
3. **Terraform**: Version >= 1.5.0
4. **gcloud CLI**: Installed and authenticated (for local development)

## Directory Structure

```
terraform/
├── main.tf                    # Provider configuration
├── storage.tf                 # Storage bucket resources
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example variables file
├── .gitignore                 # Terraform-specific gitignore
└── README.md                  # This file
```

## Local Development

### Setup

1. **Copy the example variables file**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars`** with your values:
   ```hcl
   project_id            = "your-gcp-project-id"
   region                = "us-central1"
   environment           = "dev"
   service_account_email = "your-service-account@your-project.iam.gserviceaccount.com"
   ```

3. **Authenticate with GCP**:
   ```bash
   gcloud auth application-default login
   ```

### Terraform Commands

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform (downloads providers)
terraform init

# Format code
terraform fmt

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply changes
terraform apply

# Show current state
terraform show

# List outputs
terraform output

# Destroy resources (use with caution!)
terraform destroy
```

## CI/CD Deployment

The infrastructure is automatically deployed via GitHub Actions when changes are merged to the `main` branch.

### Workflow Steps

1. **Trigger**: Push to `main` branch
2. **Tests**: All CI tests must pass
3. **Terraform Deployment**:
   - Format check
   - Initialize Terraform
   - Validate configuration
   - Plan changes
   - Apply changes
   - Upload outputs as artifacts

### Required GitHub Secrets (DEV Environment)

The following secrets must be configured in the DEV environment:

- `GCP_SA_KEY`: Service account JSON key
- `GCP_PROJECT_ID`: GCP project ID
- `GCP_SERVICE_ACCOUNT_EMAIL`: Service account email address

### Viewing Deployment Results

```bash
# Watch the workflow
gh run watch

# View latest run
gh run view

# Download outputs artifact
gh run download --name terraform-outputs
```

## Resources

### Storage Bucket

**Resource**: `google_storage_bucket.kalshihub_data`

**Features**:
- **Versioning**: Enabled for data protection
- **Lifecycle Management**:
  - Objects older than 90 days are deleted
  - Objects older than 30 days moved to NEARLINE storage class
- **Uniform Bucket-Level Access**: Enabled for simplified IAM
- **IAM**: Service account granted `storage.objectAdmin` role

**Naming**: `{project_id}-kalshihub-data`

## Variables

| Variable | Description | Type | Default | Required |
|----------|-------------|------|---------|----------|
| `project_id` | GCP project ID | string | - | Yes |
| `region` | GCP region for resources | string | `us-central1` | No |
| `environment` | Environment name (dev/staging/prod) | string | `dev` | No |
| `service_account_email` | Service account email for IAM | string | - | Yes |

## Outputs

| Output | Description |
|--------|-------------|
| `storage_bucket_name` | Name of the created storage bucket |
| `storage_bucket_url` | URL of the storage bucket |
| `storage_bucket_location` | Location of the storage bucket |

## State Management

### Local State

By default, Terraform state is stored locally in `terraform.tfstate`. This is suitable for development but **not recommended for production**.

### Remote State (Recommended)

For team environments and production, configure remote state storage:

1. **Create a state bucket manually** (one-time setup):
   ```bash
   gsutil mb gs://kalshihub-terraform-state
   gsutil versioning set on gs://kalshihub-terraform-state
   ```

2. **Uncomment the backend configuration in `main.tf`**:
   ```hcl
   backend "gcs" {
     bucket = "kalshihub-terraform-state"
     prefix = "terraform/state"
   }
   ```

3. **Migrate state**:
   ```bash
   terraform init -migrate-state
   ```

## Best Practices

1. **Always run `terraform plan` before `apply`**: Review changes before applying
2. **Use workspaces for multiple environments**: Separate dev/staging/prod
3. **Version control**: Never commit `terraform.tfvars` or state files
4. **Remote state**: Use GCS backend for team collaboration
5. **Lock files**: Commit `.terraform.lock.hcl` for consistency
6. **Variables**: Use variables for all configurable values
7. **Outputs**: Export important resource attributes
8. **IAM**: Follow principle of least privilege

## Troubleshooting

### Authentication Errors

```bash
# Re-authenticate
gcloud auth application-default login

# Verify service account
gcloud auth list
```

### State Lock Issues

If state is locked:
```bash
# Force unlock (use with caution!)
terraform force-unlock LOCK_ID
```

### Permission Denied

Ensure the service account has the required roles:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/storage.admin"
```

## Adding New Resources

1. Create a new `.tf` file (e.g., `compute.tf`)
2. Define resources with appropriate variables
3. Add outputs in `outputs.tf`
4. Update this README with resource documentation
5. Run `terraform plan` to validate
6. Submit PR with changes

## Support

For issues or questions:
- Review [Terraform GCP Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- Check [GitHub Actions logs](https://github.com/allengeer/kalshihub/actions)
- Create an issue on GitHub
