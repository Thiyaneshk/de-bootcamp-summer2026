# Phase 9: HashiCorp Terraform IaaS

## Overview

In this final phase, we use Terraform to provision and manage all cloud infrastructure (Snowflake schemas, Databricks clusters, GCP Redis instances, and Airflow VMs).
We also replace manual setup steps with a unified `Makefile`.

**Time to Complete:** 1.5 hours
**Tech Stack:** HashiCorp Terraform, Makefile

---

## What We Built

1. **Terraform Architecture:**
   - `terraform/main.tf` defines the root module and configures the GCS backend.
   - `terraform/modules/` separates components into `snowflake`, `databricks`, `redis`, and `compute`.
2. **Makefile:** Replaced manual Docker and `uv run` commands with standard Make commands.
3. **VM Startup Script:** Included a `startup.sh` script to install Docker on our GCP compute instance automatically.

---

## Validation / Acceptance Criteria

1. **Initialization:** Run `make infra-init` and verify providers (GCP, Snowflake, Databricks) are downloaded successfully.
2. **Plan:** Copy `terraform.tfvars.example` to `terraform.tfvars`, fill in the values, and run `make infra-plan`. You should see resources set for creation.
3. **Make commands:** Ensure `make dev-up` still successfully spins up the Docker compose stack locally.

---

## Completion

Congratulations, you've completed all 9 phases of the Data Engineering Bootcamp project! You've built a robust, scalable system that incorporates modern technologies spanning ingestion, distributed processing, caching, cloud data warehousing, orchestration, AI (RAG), and Infrastructure as Code.
