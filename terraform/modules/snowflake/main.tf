terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.87"
    }
  }
}

resource "snowflake_database" "bootcamp" {
  name    = var.database_name
  comment = "DE Bootcamp Summer 2026"
}

resource "snowflake_warehouse" "compute" {
  name           = var.warehouse_name
  warehouse_size = "x-small"
  auto_suspend   = 60
  auto_resume    = true
}

resource "snowflake_schema" "raw" {
  database = snowflake_database.bootcamp.name
  name     = "RAW"
}

resource "snowflake_schema" "marts" {
  database = snowflake_database.bootcamp.name
  name     = "MARTS"
}
