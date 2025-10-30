# Google Cloud Storage bucket for application data
resource "google_storage_bucket" "kalshihub_data" {
  name          = "${var.project_id}-kalshihub-data"
  location      = var.region
  force_destroy = false

  # Uniform bucket-level access
  uniform_bucket_level_access = true

  # Versioning for data protection
  versioning {
    enabled = true
  }

  # Lifecycle rules
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  # Labels for organization
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = "kalshihub"
  }
}

# IAM binding for the storage bucket
resource "google_storage_bucket_iam_member" "kalshihub_data_admin" {
  bucket = google_storage_bucket.kalshihub_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_email}"
}
