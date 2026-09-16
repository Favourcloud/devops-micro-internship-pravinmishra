output "public_url" {
  description = "HTTP-only lab URL. Use synthetic data only; TLS is not provisioned by this module."
  value       = "http://${aws_lb.public.dns_name}"
}

output "replica_identifier" {
  value = aws_db_instance.replica.identifier
}

output "replica_endpoint" {
  description = "Private replica endpoint for authorized verification, not an automatic application read route."
  value       = aws_db_instance.replica.endpoint
  sensitive   = true
}
