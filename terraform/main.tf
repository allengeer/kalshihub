terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Backend configuration for remote state storage in GCS
  # Uses the kalshihub_data bucket for state storage
  backend "gcs" {
    bucket = ""  # Will be set via backend-config flag: {project_id}-kalshihub-data
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
