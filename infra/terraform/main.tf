terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.6.2"
    }
  }
}

provider "docker" {}

resource "docker_network" "saga_net" {
  name = "saga-net"
}

resource "docker_container" "rabbitmq" {
  image = var.rabbitmq_image
  name  = var.rabbitmq_container_name
  ports {
    internal = var.amqp_port
    external = var.amqp_port
  }
  ports {
    internal = var.ui_port
    external = var.ui_port
  }
  networks_advanced {
    name = docker_network.saga_net.name
  }
}

