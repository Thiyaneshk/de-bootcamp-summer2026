terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.38"
    }
  }
}

resource "databricks_cluster" "bootcamp" {
  cluster_name            = "bootcamp-cluster"
  spark_version           = "15.4.x-scala2.12"
  node_type_id            = "Standard_DS3_v2"
  autotermination_minutes = 30

  autoscale {
    min_workers = 1
    max_workers = 3
  }
}
