output "ec2_instance_id" {
  value       = module.ec2.instance_id
  description = "Private operations inventory: instance ID for exact-ID checks."
}
output "ec2_public_ip" {
  value       = module.ec2.public_ip
  description = "Public IP, assigned only by a future authorized apply."
}
output "rds_endpoint" {
  value       = module.rds.endpoint
  description = "Private RDS DNS endpoint and port (not a public database)."
}
output "application_url" {
  value       = "http://${module.ec2.public_ip}"
  description = "Future HTTP lab URL; no production TLS/authentication promise."
}
