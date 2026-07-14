#!/bin/bash
# Simple startup script for Airflow VM
apt-get update
apt-get install -y docker.io docker-compose
systemctl enable docker
systemctl start docker
