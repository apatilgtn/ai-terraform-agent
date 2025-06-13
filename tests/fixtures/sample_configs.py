
# tests/fixtures/sample_configs.py
"""Sample configurations for testing."""

SAMPLE_VM_CONFIG = {
    "resource_type": "gcp_vm",
    "resource_name": "web_server",
    "instance_name": "web-server-01",
    "machine_type": "e2-standard-2",
    "image": "ubuntu-os-cloud/ubuntu-2004-lts",
    "disk_size": 50,
    "zone": "us-central1-a",
    "project_id": "my-gcp-project",
    "region": "us-central1",
    "environment": "production",
    "timestamp": "20240101120000",
    "metadata": 'enable-oslogin = "true"',
    "tags": '["web-server", "production"]',
    "instruction": "Create a medium Ubuntu web server"
}

SAMPLE_STORAGE_CONFIG = {
    "resource_type": "gcp_storage",
    "resource_name": "backup_bucket",
    "bucket_name": "my-backup-bucket-12345",
    "location": "EU",
    "versioning": "true",
    "project_id": "my-gcp-project",
    "region": "europe-west1",
    "environment": "production",
    "timestamp": "20240101120000",
    "instruction": "Create a backup storage bucket in Europe"
}

SAMPLE_NETWORK_CONFIG = {
    "resource_type": "gcp_network",
    "resource_name": "prod_network",
    "network_name": "production-vpc",
    "auto_create_subnets": "false",
    "cidr_range": "10.0.0.0/16",
    "region": "us-central1",
    "allowed_ports": '["22", "80", "443"]',
    "source_ranges": '["0.0.0.0/0"]',
    "target_tags": '["web-server"]',
    "project_id": "my-gcp-project",
    "environment": "production",
    "timestamp": "20240101120000",
    "instruction": "Create a production VPC network"
}
