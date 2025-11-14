variable "rabbitmq_image" {
  type        = string
  default     = "rabbitmq:3-management"
  description = "Versión de la imagen de RabbitMQ"
}

variable "rabbitmq_container_name" {
  type        = string
  default     = "local-rabbitmq"
  description = "Nombre del contenedor de RabbitMQ"
}

variable "amqp_port" {
  type    = number
  default = 5672
  description = "Puerto AMQP para RabbitMQ"
}

variable "ui_port" {
  type    = number
  default = 15672
  description = "Puerto de la interfaz de usuario de RabbitMQ"
}