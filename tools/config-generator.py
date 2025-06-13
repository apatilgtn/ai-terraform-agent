
#!/usr/bin/env python3
# tools/config-generator.py
"""
Configuration Generator Tool
Generates sample configurations and test data
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class ConfigGenerator:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    def generate_sample_configs(self) -> Dict[str, Dict[str, Any]]:
        """Generate sample configurations for testing"""
        return {
            "vm_small": {
                "resource_type": "gcp_vm",
                "resource_name": "web_server",
                "instance_name": "web-server-small",
                "machine_type": "e2-micro",
                "image": "ubuntu-os-cloud/ubuntu-2004-lts",
                "disk_size": 20,
                "zone": "us-central1-a",
                "project_id": "sample-project-123456",
                "region": "us-central1",
                "environment": "development",
                "timestamp": self.timestamp,
                "metadata": 'startup-script = "#!/bin/bash\\napt update\\napt install -y nginx"',
                "tags": '["web-server", "development"]',
                "instruction": "Create a small Ubuntu web server"
            },
            
            "vm_large": {
                "resource_type": "gcp_vm",
                "resource_name": "app_server",
                "instance_name": "app-server-large",
                "machine_type": "e2-standard-4",
                "image": "centos-cloud/centos-7",
                "disk_size": 100,
                "zone": "us-west1-a",
                "project_id": "sample-project-123456",
                "region": "us-west1",
                "environment": "production",
                "timestamp": self.timestamp,
                "metadata": 'enable-oslogin = "true"\\nstartup-script = "yum update -y"',
                "tags": '["app-server", "production", "high-memory"]',
                "instruction": "Create a large CentOS application server with 100GB disk"
            },
            
            "storage_bucket": {
                "resource_type": "gcp_storage",
                "resource_name": "data_bucket",
                "bucket_name": f"data-bucket-{self.timestamp}",
                "location": "EU",
                "versioning": "true",
                "project_id": "sample-project-123456",
                "region": "europe-west1",
                "environment": "production",
                "timestamp": self.timestamp,
                "instruction": "Create a versioned storage bucket in Europe for data backups"
            },
            
            "vpc_network": {
                "resource_type": "gcp_network",
                "resource_name": "private_network",
                "network_name": "private-vpc",
                "auto_create_subnets": "false",
                "cidr_range": "10.0.0.0/16",
                "region": "us-central1",
                "allowed_ports": '["22", "80", "443", "3306"]',
                "source_ranges": '["10.0.0.0/8"]',
                "target_tags": '["database", "web-server"]',
                "project_id": "sample-project-123456",
                "environment": "production",
                "timestamp": self.timestamp,
                "instruction": "Create a private VPC network for database and web servers"
            }
        }
    
    def generate_test_instructions(self) -> Dict[str, str]:
        """Generate test instructions for different scenarios"""
        return {
            "simple_vm": "Create a small Ubuntu VM instance named test-server",
            "web_server": "Create a medium Ubuntu VM with HTTP and HTTPS firewall rules",
            "database_server": "Create a large CentOS VM with 200GB disk for database hosting",
            "storage_bucket": "Create a storage bucket in Asia with versioning enabled",
            "backup_bucket": "Create a private storage bucket for backup data in Europe",
            "vpc_network": "Create a VPC network with subnet 10.1.0.0/24 and firewall rules",
            "private_network": "Create a private network for database servers with restricted access",
            "multi_region": "Create a VM instance in asia-southeast1 with 50GB disk",
            "development_env": "Create a small development VM with SSH access only",
            "production_web": "Create a production web server with load balancer ready configuration"
        }
    
    def generate_environment_configs(self) -> Dict[str, Dict[str, str]]:
        """Generate environment-specific configurations"""
        return {
            "development": {
                "GITHUB_REPO": "terraform-dev",
                "GCP_PROJECT_ID": "dev-project-123456",
                "LOG_LEVEL": "DEBUG",
                "ENVIRONMENT": "development"
            },
            
            "staging": {
                "GITHUB_REPO": "terraform-staging", 
                "GCP_PROJECT_ID": "staging-project-123456",
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": "staging"
            },
            
            "production": {
                "GITHUB_REPO": "terraform-infrastructure",
                "GCP_PROJECT_ID": "prod-project-123456", 
                "LOG_LEVEL": "WARNING",
                "ENVIRONMENT": "production"
            }
        }
    
    def save_configs(self, output_dir: str = "generated-configs"):
        """Save all generated configurations to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save sample configurations
        configs = self.generate_sample_configs()
        with open(output_path / "sample_configs.json", "w") as f:
            json.dump(configs, f, indent=2)
        
        with open(output_path / "sample_configs.yaml", "w") as f:
            yaml.dump(configs, f, default_flow_style=False, indent=2)
        
        # Save test instructions
        instructions = self.generate_test_instructions()
        with open(output_path / "test_instructions.json", "w") as f:
            json.dump(instructions, f, indent=2)
        
        # Save environment configs
        env_configs = self.generate_environment_configs()
        for env_name, config in env_configs.items():
            env_file = output_path / f".env.{env_name}"
            with open(env_file, "w") as f:
                for key, value in config.items():
                    f.write(f"{key}={value}\n")
        
        print(f"✅ Generated configurations saved to {output_path}/")
        return output_path
    
    def generate_kubernetes_configs(self) -> Dict[str, str]:
        """Generate Kubernetes configuration examples"""
        configs = {}
        
        # Development namespace
        configs["dev-namespace.yaml"] = """
apiVersion: v1
kind: Namespace
metadata:
  name: terraform-agent-dev
  labels:
    environment: development
    app: terraform-agent
"""
        
        # ConfigMap for development
        configs["dev-configmap.yaml"] = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: terraform-agent-config
  namespace: terraform-agent-dev
data:
  LOG_LEVEL: "DEBUG"
  ENVIRONMENT: "development"
  GITHUB_REPO: "terraform-dev"
  TIMESTAMP: "{self.timestamp}"
"""
        
        return configs

def main():
    parser = argparse.ArgumentParser(description="Generate sample configurations")
    parser.add_argument(
        "--output-dir",
        default="generated-configs",
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "both"],
        default="both",
        help="Output format"
    )
    parser.add_argument(
        "--kubernetes",
        action="store_true",
        help="Generate Kubernetes configurations"
    )
    
    args = parser.parse_args()
    
    generator = ConfigGenerator()
    output_path = generator.save_configs(args.output_dir)
    
    if args.kubernetes:
        k8s_configs = generator.generate_kubernetes_configs()
        k8s_path = output_path / "kubernetes"
        k8s_path.mkdir(exist_ok=True)
        
        for filename, content in k8s_configs.items():
            with open(k8s_path / filename, "w") as f:
                f.write(content)
        
        print(f"✅ Kubernetes configurations saved to {k8s_path}/")
    
    print("\n📋 Generated files:")
    for file_path in sorted(output_path.rglob("*")):
        if file_path.is_file():
            print(f"  - {file_path}")

if __name__ == "__main__":
    main()
