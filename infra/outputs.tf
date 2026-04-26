output "ec2_public_ip" {
  value = aws_instance.app.public_ip
}

output "ec2_public_dns" {
  value = aws_instance.app.public_dns
}

output "backup_bucket_name" {
  value = aws_s3_bucket.db_backups.bucket
}
