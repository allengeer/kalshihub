output "storage_bucket_name" {
  description = "The name of the storage bucket (also used for Terraform state)"
  value       = google_storage_bucket.kalshihub_data.name
}

output "storage_bucket_url" {
  description = "The URL of the storage bucket"
  value       = google_storage_bucket.kalshihub_data.url
}

output "storage_bucket_location" {
  description = "The location of the storage bucket"
  value       = google_storage_bucket.kalshihub_data.location
}

output "market_crawler_function_url" {
  description = "The URL of the market crawler Cloud Function"
  value       = google_cloudfunctions2_function.market_crawler.service_config[0].uri
}

output "market_crawler_function_name" {
  description = "The name of the market crawler Cloud Function"
  value       = google_cloudfunctions2_function.market_crawler.name
}
