# Cloud Monitoring Dashboards
# Version: 1.0
# Owner: Platform Team

# Gateway Performance Dashboard
resource "google_monitoring_dashboard" "gateway_performance" {
  dashboard_json = jsonencode({
    displayName = "API Gateway Performance - ${var.environment}"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Request Rate (per minute)"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_RATE"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["resource.service_name"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
              yAxis = {
                label = "Requests/min"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Response Time (p50, p95, p99)"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_DELTA"
                        crossSeriesReducer = "REDUCE_PERCENTILE_50"
                        groupByFields      = ["resource.service_name"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_DELTA"
                        crossSeriesReducer = "REDUCE_PERCENTILE_95"
                        groupByFields      = ["resource.service_name"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesQuery = {
                      filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_DELTA"
                        crossSeriesReducer = "REDUCE_PERCENTILE_99"
                        groupByFields      = ["resource.service_name"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Error Rate (%)"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_RATE"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["resource.service_name"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
              yAxis = {
                label = "Errors/min"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          xPos   = 6
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Container Instance Count"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/instance_count\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_MEAN"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["resource.service_name"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
              yAxis = {
                label = "Instances"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}

# Budget Tracking Dashboard
resource "google_monitoring_dashboard" "gateway_budget" {
  dashboard_json = jsonencode({
    displayName = "API Gateway Budget Tracking - ${var.environment}"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Platform Budget (Monthly)"
            scorecard = {
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"custom.googleapis.com/gateway/platform_budget_spent\" AND resource.type=\"global\""
                  aggregation = {
                    alignmentPeriod    = "3600s"
                    perSeriesAligner   = "ALIGN_MAX"
                  }
                }
              }
              gaugeView = {
                lowerBound = 0
                upperBound = 100
              }
              thresholds = [
                {
                  value = 80
                  color = "YELLOW"
                },
                {
                  value = 95
                  color = "RED"
                }
              ]
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Agent Budget (Daily)"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/gateway/agent_budget_spent\" AND resource.type=\"global\""
                      aggregation = {
                        alignmentPeriod    = "3600s"
                        perSeriesAligner   = "ALIGN_MAX"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["metric.agent_id"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
              yAxis = {
                label = "Spent (USD)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          yPos   = 4
          width  = 12
          height = 4
          widget = {
            title = "Rate Limit Violations"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/gateway/rate_limit_exceeded\" AND resource.type=\"global\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_RATE"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["metric.customer_id"]
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
              yAxis = {
                label = "Violations/min"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}

# Alert Policy - High Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "Gateway High Error Rate - ${var.environment}"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 1%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10  # More than 10 errors per minute
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "1800s"
  }
}

# Alert Policy - High Latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "Gateway High Latency - ${var.environment}"
  combiner     = "OR"
  
  conditions {
    display_name = "p95 latency > 200ms"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\" AND resource.labels.service_name=monitoring.regex.full_match(\"api-gateway-(cp|pp)-${var.environment}\")"
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 200  # 200ms
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "1800s"
  }
}

# Alert Policy - Budget Threshold
resource "google_monitoring_alert_policy" "budget_threshold_95" {
  display_name = "Gateway Budget 95% Threshold - ${var.environment}"
  combiner     = "OR"
  
  conditions {
    display_name = "Platform budget > 95%"
    
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/gateway/platform_budget_spent\" AND resource.type=\"global\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 95
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "3600s"
  }
}

# Variables for notification
variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}
