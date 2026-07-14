variable "project_id" { type = string }
variable "region" { type = string }

resource "google_redis_instance" "cache" {
  project        = var.project_id
  name           = "bootcamp-cache"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region
  redis_version  = "REDIS_7_0"

  labels = {
    project = "de-bootcamp"
    env     = "dev"
  }
}

output "redis_host" {
  value = google_redis_instance.cache.host
}
