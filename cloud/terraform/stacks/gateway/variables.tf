variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "environment" {
  description = "Environment (demo, uat, prod)"
  type        = string
}

variable "artifact_registry" {
  description = "Artifact Registry base URL"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
}
