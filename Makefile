RELEASE ?= 1.0.0
DIST_DIR := dist
SRC_DIR := src
TEST_DIR := tests
INFRA_DIR := infra

.PHONY: help tools plan apply run test pack clean

help: ## Muestra los targets disponibles
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':|##' '{printf "  %-12s %s\n", $$1, $$3}'

build: ## Crear un entorno virtual para el proyecto
	@python3 -m venv venv && ./venv/bin/activate

tools: ## Instalar las dependencias necesarias para el proyecto
	@pip install -r requirements.txt

plan: ## Mostrar el plan de ejecución de Terraform y los recursos que se crearán
	@cd $(INFRA_DIR)/terraform && terraform init && terraform plan

apply: ## Aplicar el plan de ejecución de Terraform creando los recursos de la infraestructura
	@cd $(INFRA_DIR)/terraform && terraform apply -auto-approve

run: plan apply ## Ejecutar el orquestador saga
	@python3 $(SRC_DIR)/saga/initialize_databases.py
	@python3 $(SRC_DIR)/saga/orchestrator.py

test: ## Ejecutar pruebas unitarias y pruebas end to end (e2e)
	@pytest $(TEST_DIR)

pack: ## Empaqueta el release del proyecto
	@mkdir -p $(DIST_DIR)
	@tar -czf $(DIST_DIR)/SAGA-Orquestrator-$(RELEASE).tar.gz $(SRC_DIR) $(TEST_DIR) $(INFRA_DIR) $(DOCS_DIR) Makefile .gitignore README.md requirements.txt

clean: ## Limpiar archivos generados
	@rm -rf $(DIST_DIR)
	@cd $(INFRA_DIR)/terraform && terraform destroy -auto-approve
	@cd $(SRC_DIR)/saga && python3 clean_databases.py