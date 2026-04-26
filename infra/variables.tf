variable "project_name" {
  type    = string
  default = "english-study-app"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "ami_id" {
  type        = string
  description = "AMI Ubuntu 22.04"
}

variable "key_name" {
  type        = string
  description = "Nome da chave SSH da EC2"
}

variable "allowed_ssh_cidr" {
  type        = string
  description = "CIDR permitido para SSH"
}
