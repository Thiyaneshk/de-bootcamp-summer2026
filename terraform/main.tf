terraform {
  required_version = ">= 1.7"
  required_providers {
    google     = { source = "hashicorp/google",          version = "~> 5.0" }
    snowflake  = { source = "Snowflake-Labs/snowflake",  version = "~> 0.87" }
    databricks = { source = "databricks/databricks",     version = "~> 1.38" }
  }

  backend "gcs" {
    bucket = "bootcamp-tf-state"
    prefix = "terraform/state"
  }
}

module "snowflake" {
  source         = "./modules/snowflake"
  database_name  = var.snowflake_database
  warehouse_name = var.snowflake_warehouse
}

module "databricks" {
  source = "./modules/databricks"
}

module "redis" {
  source     = "./modules/redis"
  project_id = var.gcp_project_id
  region     = var.gcp_region
}

module "compute" {
  source     = "./modules/compute"
  project_id = var.gcp_project_id
  region     = var.gcp_region
}
