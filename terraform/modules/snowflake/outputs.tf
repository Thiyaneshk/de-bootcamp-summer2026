output "database_name" {
  value = snowflake_database.bootcamp.name
}

output "warehouse_name" {
  value = snowflake_warehouse.compute.name
}
