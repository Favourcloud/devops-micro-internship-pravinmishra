variable "name" { type = string }
variable "enable_initializer" { type = bool }
variable "load_balancer_dimensions" { type = map(map(string)) }
variable "replica_identifier" { type = string }
resource "aws_cloudwatch_log_group" "tier" {
  for_each          = var.enable_initializer ? toset(["web", "app", "initializer"]) : toset(["web", "app"])
  name              = "/dmi/${var.name}/${each.key}"
  retention_in_days = 7
}
resource "aws_cloudwatch_metric_alarm" "unhealthy" {
  for_each            = var.load_balancer_dimensions
  alarm_name          = "${var.name}-${each.key}-unhealthy"
  alarm_description   = "Inspect private readiness; no notification subscription is configured."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "breaching"
  dimensions          = each.value
}
resource "aws_cloudwatch_metric_alarm" "replica_lag" {
  alarm_name          = "${var.name}-replica-lag"
  namespace           = "AWS/RDS"
  metric_name         = "ReplicaLag"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 60
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "breaching"
  dimensions          = { DBInstanceIdentifier = var.replica_identifier }
}
output "log_group_arns" { value = { for tier, group in aws_cloudwatch_log_group.tier : tier => group.arn } }
