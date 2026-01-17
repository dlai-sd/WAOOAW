output "job_name" {
  description = "Name of the Cloud Run Job"
  value       = google_cloud_run_v2_job.job.name
}

output "job_id" {
  description = "Full resource ID of the job"
  value       = google_cloud_run_v2_job.job.id
}

output "job_uri" {
  description = "URI to view the job in GCP console"
  value       = "https://console.cloud.google.com/run/jobs/details/${var.region}/${google_cloud_run_v2_job.job.name}?project=${var.project_id}"
}
