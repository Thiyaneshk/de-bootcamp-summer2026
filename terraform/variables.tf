variable "gcp_project_id"      { type = string }
variable "gcp_region"           { default = "northamerica-northeast2" }  # Toronto
variable "snowflake_database"   { default = "BOOTCAMP_DB" }
variable "snowflake_warehouse"  { default = "COMPUTE_WH" }
variable "snowflake_account"    { type = string, default = "" }
