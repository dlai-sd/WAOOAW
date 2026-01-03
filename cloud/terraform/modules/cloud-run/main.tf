resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region
  project  = var.project_id
  
  labels = {
    environment  = var.environment
    service-type = var.service_type
    managed-by   = "terraform"
  }
  
  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    containers {
      image = var.image
      
      ports {
        name           = "http1"
        container_port = var.port
      }
      
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        
        cpu_idle          = true
        startup_cpu_boost = true
      }
      
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
      
      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = split(":", env.value)[0]
              version = split(":", env.value)[1]
            }
          }
        }
      }
    }
    
    timeout = "30s"
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image  # Allow manual image updates
    ]
  }
}

# Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
