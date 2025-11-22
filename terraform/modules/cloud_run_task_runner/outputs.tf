output "job_name" {
  value = google_cloud_run_v2_job.task_runner.name
}

output "location" {
  value = google_cloud_run_v2_job.task_runner.location
}

output "job_id" {
  value = google_cloud_run_v2_job.task_runner.id
}
