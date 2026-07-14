.PHONY: infra-init infra-plan infra-apply infra-destroy dev-up dev-down dbt-run dbt-test

infra-init:
	cd terraform && terraform init

infra-plan:
	cd terraform && terraform plan -var-file=terraform.tfvars

infra-apply:
	cd terraform && terraform apply -var-file=terraform.tfvars

infra-destroy:
	cd terraform && terraform destroy -var-file=terraform.tfvars

dev-up:
	docker-compose up -d

dev-down:
	docker-compose down

dbt-run:
	uv run dbt run --profiles-dir dbt --target snowflake

dbt-test:
	uv run dbt test --profiles-dir dbt --target snowflake
