variable "api_id" { type = string }
variable "name" { type = string }
variable "web_subnets" { type = list(string) }
variable "security_group_id" { type = string }
variable "listener_arn" { type = string }
resource "aws_apigatewayv2_vpc_link" "this" {
  name               = "${var.name}-private-link"
  subnet_ids         = var.web_subnets
  security_group_ids = [var.security_group_id]
}
resource "aws_apigatewayv2_integration" "this" {
  api_id                 = var.api_id
  integration_type       = "HTTP_PROXY"
  integration_method     = "ANY"
  integration_uri        = var.listener_arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.this.id
  payload_format_version = "1.0"
  timeout_milliseconds   = 30000
  request_parameters = {
    "overwrite:path"                     = "$request.path"
    "overwrite:header.x-a5-viewer-proto" = "https"
    "overwrite:header.x-a5-viewer-host"  = "$context.domainName"
  }
}
resource "aws_apigatewayv2_route" "this" {
  api_id    = var.api_id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.this.id}"
}
output "id" { value = aws_apigatewayv2_vpc_link.this.id }
