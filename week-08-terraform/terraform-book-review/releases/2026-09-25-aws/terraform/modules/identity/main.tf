variable "name" { type = string }
variable "tier" { type = string }
variable "secret_arns" {
  type    = list(string)
  default = []
}
variable "log_group_arn" { type = string }
resource "aws_iam_role" "this" {
  name_prefix = "${var.name}-${var.tier}-"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_instance_profile" "this" {
  name_prefix = "${var.name}-${var.tier}-"
  role        = aws_iam_role.this.name
}
resource "aws_iam_role_policy" "this" {
  name = "scoped-runtime"
  role = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Sid      = "SessionManagerChannels"
        Effect   = "Allow"
        Action   = ["ssm:UpdateInstanceInformation", "ssmmessages:CreateControlChannel", "ssmmessages:CreateDataChannel", "ssmmessages:OpenControlChannel", "ssmmessages:OpenDataChannel"]
        Resource = "*"
      },
      {
        Sid      = "ProjectLogStreamsOnly"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${var.log_group_arn}:*"
      }
      ], length(var.secret_arns) == 0 ? [] : [{
        Sid      = "ExactRuntimeSecretsOnly"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = var.secret_arns
    }])
  })
}
output "profile_name" { value = aws_iam_instance_profile.this.name }
output "role_arn" { value = aws_iam_role.this.arn }
output "policy" { value = aws_iam_role_policy.this.policy }
