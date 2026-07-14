variable "project_id" { type = string }
variable "region" { type = string }

resource "google_compute_instance" "airflow_vm" {
  project      = var.project_id
  name         = "bootcamp-airflow"
  machine_type = "e2-medium"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 50
    }
  }

  network_interface {
    network = "default"
    access_config {}  # Ephemeral public IP
  }

  metadata_startup_script = file("${path.module}/startup.sh")

  tags = ["http-server", "https-server"]
}

output "airflow_vm_ip" {
  value = google_compute_instance.airflow_vm.network_interface[0].access_config[0].nat_ip
}
