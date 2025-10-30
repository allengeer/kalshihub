# Google Cloud Function for engine admin
# This function provides administrative operations for various systems

# Archive the function code with proper structure
data "archive_file" "engine_admin_function" {
  type        = "zip"
  output_path = "${path.module}/engine_admin_function.zip"

  # Include requirements.txt at root
  source {
    content  = file("${path.module}/../src/functions/engine_admin/requirements.txt")
    filename = "requirements.txt"
  }

  # Include main.py at root
  source {
    content  = file("${path.module}/../src/functions/engine_admin/main.py")
    filename = "main.py"
  }

  # Include all Python files from src/ (except the functions dir itself)
  dynamic "source" {
    for_each = fileset("${path.module}/../src", "**/*.py")
    content {
      content  = file("${path.module}/../src/${source.value}")
      # Don't duplicate main.py from functions/engine_admin
      filename = source.value == "functions/engine_admin/main.py" ? ".ignore" : source.value
    }
  }
}

# Upload function source to storage bucket
resource "google_storage_bucket_object" "engine_admin_function" {
  name   = "functions/engine_admin-${data.archive_file.engine_admin_function.output_md5}.zip"
  bucket = google_storage_bucket.kalshihub_data.name
  source = data.archive_file.engine_admin_function.output_path
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "engine_admin" {
  name        = "engine-admin"
  location    = var.region
  description = "Administrative operations for engine systems"

  build_config {
    runtime     = "python313"
    entry_point = "engine_admin"
    source {
      storage_source {
        bucket = google_storage_bucket.kalshihub_data.name
        object = google_storage_bucket_object.engine_admin_function.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    min_instance_count    = 0
    available_memory      = "2Gi"
    available_cpu         = "1"
    timeout_seconds       = 540
    service_account_email = var.service_account_email

    environment_variables = {
      FIREBASE_PROJECT_ID = var.project_id
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = "kalshihub"
  }
}

# IAM member to allow authenticated invocation
resource "google_cloudfunctions2_function_iam_member" "engine_admin_invoker" {
  project        = google_cloudfunctions2_function.engine_admin.project
  location       = google_cloudfunctions2_function.engine_admin.location
  cloud_function = google_cloudfunctions2_function.engine_admin.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${var.service_account_email}"
}
