variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "static_ip_name" {
  description = "Name of the existing global static IP address"
  type        = string
  default     = "waooaw-lb-ip"
}

variable "enable_cp" {
  description = "Include CP hostnames/routing"
  type        = bool
  default     = true
}

variable "enable_pp" {
  description = "Include PP hostnames/routing"
  type        = bool
  default     = false
}

variable "enable_plant" {
  description = "Include Plant hostnames/routing"
  type        = bool
  default     = false
}

variable "enabled_environments" {
  description = "Environments to include in shared LB routing (subset of demo/uat/prod)."
  type        = set(string)
  default     = ["demo"]

  validation {
    condition     = length(setsubtract(var.enabled_environments, ["demo", "uat", "prod"])) == 0
    error_message = "enabled_environments must only contain demo, uat, and/or prod."
  }

  validation {
    condition     = length(var.enabled_environments) > 0
    error_message = "enabled_environments must contain at least one environment."
  }
}

variable "domains" {
  description = "Hostname inventory for the shared load balancer"
  type = object({
    demo = object({ cp = string, pp = string, plant = string })
    uat  = object({ cp = string, pp = string, plant = string })
    prod = object({ cp = string, pp = string, plant = string })
  })

  default = {
    demo = {
      cp    = "cp.demo.waooaw.com"
      pp    = "pp.demo.waooaw.com"
      plant = "plant.demo.waooaw.com"
    }
    uat = {
      cp    = "cp.uat.waooaw.com"
      pp    = "pp.uat.waooaw.com"
      plant = "plant.uat.waooaw.com"
    }
    prod = {
      cp    = "www.waooaw.com"
      pp    = "pp.waooaw.com"
      plant = "plant.waooaw.com"
    }
  }
}
