output "url" {
  value = "http://${aws_lb.ha.dns_name}"
}
output "vpc_id" {
  value = aws_vpc.ha.id
}
output "asg_name" {
  value = aws_autoscaling_group.web.name
}
output "target_group_arn" {
  value = aws_lb_target_group.web.arn
}
output "database_identifier" {
  value = aws_db_instance.ha.identifier
}
output "subnets" {
  value = {
    public  = [for subnet in aws_subnet.public : { id = subnet.id, az = subnet.availability_zone, cidr = subnet.cidr_block }]
    private = [for subnet in aws_subnet.private : { id = subnet.id, az = subnet.availability_zone, cidr = subnet.cidr_block }]
  }
}
