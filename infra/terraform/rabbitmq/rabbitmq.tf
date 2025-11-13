terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

resource "docker_image" "rabbitmq" {
  name = var.rabbitmq_image
}

resource "docker_container" "rabbitmq" {
  name  = var.rabbitmq_container_name
  image = docker_image.rabbitmq.latest

  ports {
    internal = 5672
    external = var.amqp_port
  }

  ports {
    internal = 15672
    external = var.ui_port
  }

  restart = "always"
}
