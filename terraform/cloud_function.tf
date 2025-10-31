# Google Cloud Function for market crawler
# This function runs the market crawler once per invocation

# Archive the function code with proper structure
# Cloud Functions expects requirements.txt and main.py at the root level
data "archive_file" "market_crawler_function" {
  type        = "zip"
  output_path = "${path.module}/market_crawler_function.zip"

  # Include requirements.txt at root (from functions/market_crawler/)
  source {
    content  = file("${path.module}/../src/functions/market_crawler/requirements.txt")
    filename = "requirements.txt"
  }

  # Include main.py at root (from functions/market_crawler/)
  source {
    content  = file("${path.module}/../src/functions/market_crawler/main.py")
    filename = "main.py"
  }

  # Include all Python files from src/ (except the functions dir itself)
  dynamic "source" {
    for_each = fileset("${path.module}/../src", "**/*.py")
    content {
      content = file("${path.module}/../src/${source.value}")
      # Don't duplicate main.py from functions/market_crawler
      filename = source.value == "functions/market_crawler/main.py" ? ".ignore" : source.value
    }
  }
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
    entry_point = "crawl_markets"
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
    available_cpu         = "1"
    timeout_seconds       = 540
    service_account_email = var.service_account_email

    environment_variables = {
      FIREBASE_PROJECT_ID         = var.project_id
      KALSHI_BASE_URL             = "https://api.elections.kalshi.com/trade-api/v2"
      KALSHI_RATE_LIMIT           = "20.0"
      CRAWLER_MAX_RETRIES         = "3"
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

# Pub/Sub topic for crawl events
resource "google_pubsub_topic" "market_crawl" {
  name = "market-crawl"
  labels = {
    environment = var.environment
    application = "kalshihub"
  }
}

# Allow the service account to publish to the topic (for Cloud Scheduler)
resource "google_pubsub_topic_iam_member" "market_crawl_publisher" {
  topic  = google_pubsub_topic.market_crawl.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${var.service_account_email}"
}

# Push subscription that delivers messages to the HTTP function
resource "google_pubsub_subscription" "market_crawl_push" {
  name                 = "market-crawl-push"
  topic                = google_pubsub_topic.market_crawl.name
  ack_deadline_seconds = 600

  push_config {
    push_endpoint = google_cloudfunctions2_function.market_crawler.service_config[0].uri
    oidc_token {
      service_account_email = var.service_account_email
    }

  }

  labels = {
    environment = var.environment
    application = "kalshihub"
  }
}

# Cloud Scheduler job that publishes a crawl event every 15 minutes
resource "google_cloud_scheduler_job" "market_crawl_schedule" {
  name        = "market-crawl-every-15m"
  description = "Publish crawl event to Pub/Sub every 15 minutes"
  schedule    = "*/15 * * * *"
  time_zone   = "UTC"

  pubsub_target {
    topic_name = google_pubsub_topic.market_crawl.id
    # Request 1-day horizon via delta minutes (1440)
    data = base64encode(jsonencode({
      max_close_delta_minutes = "1440"
    }))
  }
}

# Google Cloud Function for market event processor
# This function is triggered by Firestore document writes and publishes Pub/Sub events

# Archive the function code
data "archive_file" "market_event_processor_function" {
  type        = "zip"
  output_path = "${path.module}/market_event_processor_function.zip"

  # Include requirements.txt at root
  source {
    content  = file("${path.module}/../src/functions/market_event_processor/requirements.txt")
    filename = "requirements.txt"
  }

  # Include main.py at root
  source {
    content  = file("${path.module}/../src/functions/market_event_processor/main.py")
    filename = "main.py"
  }

  # Include all Python files from src/ (except the functions dir itself)
  dynamic "source" {
    for_each = fileset("${path.module}/../src", "**/*.py")
    content {
      content = file("${path.module}/../src/${source.value}")
      # Don't duplicate main.py from functions/market_event_processor
      filename = source.value == "functions/market_event_processor/main.py" ? ".ignore" : source.value
    }
  }
}

# Upload function source to storage bucket
resource "google_storage_bucket_object" "market_event_processor_function" {
  name   = "functions/market_event_processor-${data.archive_file.market_event_processor_function.output_md5}.zip"
  bucket = google_storage_bucket.kalshihub_data.name
  source = data.archive_file.market_event_processor_function.output_path
}

# Cloud Function resource with Firestore trigger
resource "google_cloudfunctions2_function" "market_event_processor" {
  name        = "market-event-processor"
  location    = var.region
  description = "Processes Firestore market document changes and publishes Pub/Sub events"

  build_config {
    runtime     = "python313"
    entry_point = "process_market_event"
    source {
      storage_source {
        bucket = google_storage_bucket.kalshihub_data.name
        object = google_storage_bucket_object.market_event_processor_function.name
      }
    }
  }

  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "512Mi"
    available_cpu         = "1"
    timeout_seconds       = 60
    service_account_email = var.service_account_email

    environment_variables = {
      FIREBASE_PROJECT_ID = var.project_id
    }
  }

  event_trigger {
    trigger_region = "nam5"
    event_type     = "google.cloud.firestore.document.v1.written"
    retry_policy   = "RETRY_POLICY_RETRY"

    event_filters {
      attribute = "database"
      value     = "(default)"
    }

    event_filters {
      attribute = "document"
      value     = "markets/{ticker}"
      operator  = "match-path-pattern"
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = "kalshihub"
  }
}
