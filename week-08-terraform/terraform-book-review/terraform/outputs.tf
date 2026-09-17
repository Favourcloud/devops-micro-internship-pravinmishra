output "proposed_public_origin" {
  value       = local.public_origin
  description = "Proposed HTTPS origin, NOT a working/verified application URL. External DNS/certificate approval is required."
}
output "load_balancer_dns_for_approved_dns_change" {
  value       = module.load_balancing.public_dns
  description = "DNS mapping input only; never use the bare ALB hostname for credential entry."
}
output "architecture" {
  value = {
    network             = module.network.design
    security_chain      = module.security.chain
    database            = module.database.design
    web_az_groups       = module.web.az_groups
    app_az_groups       = module.app.az_groups
    initializer_enabled = var.enable_database_initializer
    runtime_authorized  = var.runtime_release_authorized
  }
}
output "source_status" {
  value = {
    assignment_complete = false
    cloud_verified      = false
    evidence_slots      = 28
    reflections_pending = 15
    upstream_commit     = "84280063bea7ccd5144dafa2b969ec4e2e69ffbb"
    public_release_gate = "Pinned dependency advisories and all human/runtime checks remain unresolved."
  }
}
