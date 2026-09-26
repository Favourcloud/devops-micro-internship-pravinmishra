# AWS-provided HTTPS address. Viewer traffic uses TLS; this demo's origin hop is HTTP.
# Move to a certificate-backed HTTPS origin before handling real personal/payment data.
resource "aws_cloudfront_distribution" "epicbook" {
  enabled     = true
  comment     = "Eze Favour DMI Week11 EpicBook"
  price_class = "PriceClass_100"
  origin {
    domain_name = "ec2-${replace(aws_eip.docker["epicbook"].public_ip, ".", "-")}.compute-1.amazonaws.com"
    origin_id   = "epicbook"
    custom_header {
      name  = "X-DMI-Viewer-Scheme"
      value = "https"
    }
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    target_origin_id       = "epicbook"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies { forward = "all" }
    }
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate { cloudfront_default_certificate = true }
}
output "https_url" { value = "https://${aws_cloudfront_distribution.epicbook.domain_name}/" }
