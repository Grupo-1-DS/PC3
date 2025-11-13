terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }

  required_version = ">= 1.3.0"
}

provider "docker" {}

module "rabbitmq" {
  source = "./rabbitmq"

  rabbitmq_image          = var.rabbitmq_image
  rabbitmq_container_name = var.rabbitmq_container_name
  amqp_port               = var.amqp_port
  ui_port                 = var.ui_port
}
