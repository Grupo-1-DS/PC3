variable "rabbitmq_image" {
  type        = string
  default     = "rabbitmq:3-management"
  description = "RabbitMQ image version"
}

variable "rabbitmq_container_name" {
  type        = string
  default     = "local-rabbitmq"
  description = "Container name"
}

variable "amqp_port" {
  type    = number
  default = 5672
}

variable "ui_port" {
  type    = number
  default = 15672
}
