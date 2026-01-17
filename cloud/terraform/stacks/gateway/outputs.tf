output "cp_gateway_url" {
  description = "CP Gateway service URL"
  value       = module.cp_gateway.service_url
}

output "pp_gateway_url" {
  description = "PP Gateway service URL"
  value       = module.pp_gateway.service_url
}

output "cp_gateway_neg" {
  description = "CP Gateway NEG for load balancer"
  value       = module.cp_gateway.neg_id
}

output "pp_gateway_neg" {
  description = "PP Gateway NEG for load balancer"
  value       = module.pp_gateway.neg_id
}
