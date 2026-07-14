output "redis_host"        { value = module.redis.redis_host }
output "airflow_vm_ip"     { value = module.compute.airflow_vm_ip }
output "snowflake_account" { value = var.snowflake_account }
