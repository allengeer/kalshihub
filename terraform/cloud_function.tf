# Google Cloud Function for market crawler
# This function runs the market crawler once per invocation

# Archive the entire src directory (includes the Cloud Function at functions/market_crawler/)
data "archive_file" "market_crawler_function" {
  type        = "zip"
  output_path = "${path.module}/market_crawler_function.zip"
  source_dir  = "${path.module}/../src"
  excludes = [
    "__pycache__",
    "**/__pycache__",
    "*.pyc",
    "**/*.pyc",
    ".pytest_cache",
    "**/.pytest_cache",
  ]
}

# Upload function source to storage bucket
resource "google_storage_bucket_object" "market_crawler_function" {
  name   = "functions/market_crawler-${data.archive_file.market_crawler_function.output_md5}.zip"
  bucket = google_storage_bucket.kalshihub_data.name
  source = data.archive_file.market_crawler_function.output_path
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "market_crawler" {
  name        = "market-crawler"
  location    = var.region
  description = "Crawls market data from Kalshi API and stores in Firebase"

  build_config {
    runtime     = "python313"
    entry_point = "functions.market_crawler.main.crawl_markets"
    source {
      storage_source {
        bucket = google_storage_bucket.kalshihub_data.name
        object = google_storage_bucket_object.market_crawler_function.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    min_instance_count    = 0
    available_memory      = "4Gi"
    timeout_seconds       = 540
    service_account_email = var.service_account_email

    environment_variables = {
      FIREBASE_PROJECT_ID        = var.project_id
      KALSHI_BASE_URL            = "https://api.elections.kalshi.com/trade-api/v2"
      KALSHI_RATE_LIMIT          = "20.0"
      CRAWLER_MAX_RETRIES        = "3"
      CRAWLER_RETRY_DELAY_SECONDS = "1"
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = "kalshihub"
  }
}

# IAM member to allow unauthenticated invocation (for Cloud Scheduler)
resource "google_cloudfunctions2_function_iam_member" "market_crawler_invoker" {
  project        = google_cloudfunctions2_function.market_crawler.project
  location       = google_cloudfunctions2_function.market_crawler.location
  cloud_function = google_cloudfunctions2_function.market_crawler.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${var.service_account_email}"
}
