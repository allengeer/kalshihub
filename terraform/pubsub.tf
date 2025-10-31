# Pub/Sub topics for event-driven architecture

# Market lifecycle events topic
resource "google_pubsub_topic" "market_events" {
  project = var.project_id
  name    = "market-events"

  labels = {
    environment = var.environment
    application = "kalshihub"
    domain       = "market"
  }
}

# Allow service account to publish to market-events
resource "google_pubsub_topic_iam_member" "market_events_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.market_events.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.service_account_email}"
}

# Crawler events topic
resource "google_pubsub_topic" "crawler_events" {
  project = var.project_id
  name    = "crawler-events"

  labels = {
    environment = var.environment
    application = "kalshihub"
    domain       = "crawler"
  }
}

# Allow service account to publish to crawler-events
resource "google_pubsub_topic_iam_member" "crawler_events_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.crawler_events.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.service_account_email}"
}

# System events topic
resource "google_pubsub_topic" "system_events" {
  project = var.project_id
  name    = "system-events"

  labels = {
    environment = var.environment
    application = "kalshihub"
    domain       = "system"
  }
}

# Allow service account to publish to system-events
resource "google_pubsub_topic_iam_member" "system_events_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.system_events.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.service_account_email}"
}
