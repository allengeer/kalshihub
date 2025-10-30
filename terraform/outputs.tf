output "storage_bucket_name" {
  description = "The name of the created storage bucket"
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
