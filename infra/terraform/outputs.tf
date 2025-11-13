output "rabbitmq_ui_url" {
  value       = "http://localhost:${var.ui_port}"
  description = "RabbitMQ UI"
}

output "rabbitmq_amqp" {
  value       = "amqp://localhost:${var.amqp_port}"
  description = "RabbitMQ AMQP connection"
}
