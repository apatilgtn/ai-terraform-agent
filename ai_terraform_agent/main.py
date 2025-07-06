#!/usr/bin/env python3
"""
AI-Assisted Terraform Agent
A FastAPI-based service that converts natural language to Terraform code,
pushes to GitHub, and creates Pull Requests.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import tempfile
import shutil

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO", "terraform-infrastructure")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Make GitHub/GCP optional for local testing
if not GITHUB_TOKEN or not GITHUB_OWNER or not GCP_PROJECT_ID:
    logger.warning("Some environment variables are missing. GitHub/GCP features may not work.")

app = FastAPI(
    title="AI Terraform Agent",
    description="Convert natural language to Terraform code and deploy via GitHub PRs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TerraformRequest(BaseModel):
    instruction: str = Field(..., description="Natural language instruction for Terraform")
    branch_name: Optional[str] = Field(None, description="Custom branch name")
    auto_merge: bool = Field(False, description="Auto-merge if checks pass")

class TerraformResponse(BaseModel):
    success: bool
    message: str
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    terraform_files: Optional[Dict[str, str]] = None

class MCPEvent(BaseModel):
    event: str
    data: Dict[str, Any]

# Fixed Terraform Templates (using .format() instead of Jinja2)
TERRAFORM_TEMPLATES = {
    "gcp_vm": """# GCP VM Instance - Generated from: {instruction}
resource "google_compute_instance" "{resource_name}" {{
  name         = "{instance_name}"
  machine_type = "{machine_type}"
  zone         = "{zone}"

  boot_disk {{
    initialize_params {{
      image = "{image}"
      size  = {disk_size}
    }}
  }}

  network_interface {{
    network = "default"
    access_config {{
      // Ephemeral public IP
    }}
  }}

  metadata = {{
    {metadata}
  }}

  tags = {tags}

  labels = {{
    environment = "{environment}"
    managed_by  = "terraform-agent"
    created_at  = "{timestamp}"
  }}
}}

output "{resource_name}_external_ip" {{
  value = google_compute_instance.{resource_name}.network_interface[0].access_config[0].nat_ip
}}

output "{resource_name}_internal_ip" {{
  value = google_compute_instance.{resource_name}.network_interface[0].network_ip
}}
""",

    "gcp_storage": """# GCP Storage Bucket - Generated from: {instruction}
resource "google_storage_bucket" "{resource_name}" {{
  name     = "{bucket_name}"
  location = "{location}"

  uniform_bucket_level_access = true

  versioning {{
    enabled = {versioning}
  }}

  labels = {{
    environment = "{environment}"
    managed_by  = "terraform-agent"
    created_at  = "{timestamp}"
  }}
}}

output "{resource_name}_url" {{
  value = google_storage_bucket.{resource_name}.url
}}
""",

    "gcp_network": """# GCP VPC Network - Generated from: {instruction}
resource "google_compute_network" "{resource_name}" {{
  name                    = "{network_name}"
  auto_create_subnetworks = {auto_create_subnets}
}}

resource "google_compute_subnetwork" "{resource_name}_subnet" {{
  name          = "{network_name}-subnet"
  ip_cidr_range = "{cidr_range}"
  region        = "{region}"
  network       = google_compute_network.{resource_name}.id
}}

resource "google_compute_firewall" "{resource_name}_firewall" {{
  name    = "{network_name}-firewall"
  network = google_compute_network.{resource_name}.name

  allow {{
    protocol = "tcp"
    ports    = {allowed_ports}
  }}

  source_ranges = {source_ranges}
  target_tags   = {target_tags}
}}

output "{resource_name}_network_id" {{
  value = google_compute_network.{resource_name}.id
}}
""",

    "provider": """terraform {{
  required_version = ">= 1.0"
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 4.0"
    }}
  }}
}}

provider "google" {{
  project = "{project_id}"
  region  = "{region}"
  zone    = "{zone}"
}}
"""
}

class KAgent:
    """Knowledge Agent - Parses natural language into Terraform configurations"""
    
    @staticmethod
    def parse_instruction(instruction: str) -> Dict[str, Any]:
        """Parse natural language instruction into structured Terraform config"""
        instruction_lower = instruction.lower()
        
        # Default values
        config = {
            "resource_type": "unknown",
            "resource_name": "main_resource",
            "environment": "dev",
            "region": "us-central1",
            "zone": "us-central1-a",
            "project_id": GCP_PROJECT_ID or "your-project-id",
            "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
            "instruction": instruction
        }
        
        # Parse VM instances
        if any(keyword in instruction_lower for keyword in ["vm", "instance", "compute", "server"]):
            config.update({
                "resource_type": "gcp_vm",
                "instance_name": KAgent._extract_name(instruction, "vm-instance"),
                "machine_type": KAgent._extract_machine_type(instruction),
                "image": KAgent._extract_image(instruction),
                "disk_size": KAgent._extract_disk_size(instruction),
                "metadata": KAgent._extract_metadata(instruction),
                "tags": KAgent._extract_tags(instruction),
            })
        
        # Parse Storage buckets
        elif any(keyword in instruction_lower for keyword in ["bucket", "storage", "blob"]):
            config.update({
                "resource_type": "gcp_storage",
                "bucket_name": KAgent._extract_name(instruction, "storage-bucket"),
                "location": KAgent._extract_location(instruction),
                "versioning": KAgent._extract_versioning(instruction),
            })
        
        # Parse Networks
        elif any(keyword in instruction_lower for keyword in ["network", "vpc", "subnet"]):
            config.update({
                "resource_type": "gcp_network",
                "network_name": KAgent._extract_name(instruction, "vpc-network"),
                "auto_create_subnets": "false",
                "cidr_range": KAgent._extract_cidr(instruction),
                "allowed_ports": KAgent._extract_ports(instruction),
                "source_ranges": '["0.0.0.0/0"]',
                "target_tags": '["web-server"]'
            })
        
        # Set resource_name based on the type
        if config["resource_type"] == "gcp_vm":
            config["resource_name"] = config["instance_name"].replace("-", "_")
        elif config["resource_type"] == "gcp_storage":
            config["resource_name"] = config["bucket_name"].replace("-", "_")
        elif config["resource_type"] == "gcp_network":
            config["resource_name"] = config["network_name"].replace("-", "_")
        
        return config
    
    @staticmethod
    def _extract_name(instruction: str, default: str) -> str:
        """Extract resource name from instruction"""
        # Look for patterns like "named X" or "called X"
        words = instruction.split()
        for i, word in enumerate(words):
            if word.lower() in ["named", "called"] and i + 1 < len(words):
                return words[i + 1].lower().replace(" ", "-")
        return f"{default}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    @staticmethod
    def _extract_machine_type(instruction: str) -> str:
        """Extract machine type from instruction"""
        if "large" in instruction.lower():
            return "e2-standard-4"
        elif "small" in instruction.lower():
            return "e2-micro"
        elif "medium" in instruction.lower():
            return "e2-standard-2"
        return "e2-micro"  # Default to cheapest option
    
    @staticmethod
    def _extract_image(instruction: str) -> str:
        """Extract OS image from instruction"""
        instruction_lower = instruction.lower()
        if "ubuntu" in instruction_lower:
            return "ubuntu-os-cloud/ubuntu-2004-lts"
        elif "centos" in instruction_lower:
            return "centos-cloud/centos-7"
        elif "windows" in instruction_lower:
            return "windows-cloud/windows-server-2019-dc-v20231114"
        return "debian-cloud/debian-11"  # Default
    
    @staticmethod
    def _extract_disk_size(instruction: str) -> int:
        """Extract disk size from instruction"""
        import re
        size_match = re.search(r'(\d+)\s*(gb|tb)', instruction.lower())
        if size_match:
            size = int(size_match.group(1))
            unit = size_match.group(2)
            return size * 1024 if unit == "tb" else size
        return 20  # Default 20GB
    
    @staticmethod
    def _extract_metadata(instruction: str) -> str:
        """Extract metadata from instruction - Fixed to avoid Jinja2 conflicts"""
        if "ssh" in instruction.lower():
            return 'enable-oslogin = "true"'
        return 'startup-script = "#!/bin/bash\\necho Hello World from Terraform Agent"'
    
    @staticmethod
    def _extract_tags(instruction: str) -> str:
        """Extract tags from instruction - Fixed to avoid Jinja2 conflicts"""
        if "web" in instruction.lower():
            return '["terraform-managed", "http-server", "https-server"]'
        return '["terraform-managed"]'
    
    @staticmethod
    def _extract_location(instruction: str) -> str:
        """Extract storage location from instruction"""
        if "europe" in instruction.lower():
            return "EU"
        elif "asia" in instruction.lower():
            return "ASIA"
        return "US"
    
    @staticmethod
    def _extract_versioning(instruction: str) -> str:
        """Extract versioning preference from instruction"""
        return "true" if "version" in instruction.lower() else "false"
    
    @staticmethod
    def _extract_cidr(instruction: str) -> str:
        """Extract CIDR range from instruction"""
        import re
        cidr_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', instruction)
        return cidr_match.group(1) if cidr_match else "10.0.0.0/24"
    
    @staticmethod
    def _extract_ports(instruction: str) -> str:
        """Extract allowed ports from instruction"""
        ports = ["22"]  # SSH always allowed
        if "web" in instruction.lower() or "http" in instruction.lower():
            ports.extend(["80", "443"])
        if "database" in instruction.lower():
            ports.append("3306")
        return json.dumps(ports)

class GitHubManager:
    """Manages GitHub operations - branches, commits, PRs"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        self.base_url = "https://api.github.com"
    
    async def create_branch(self, branch_name: str) -> bool:
        """Create a new branch from main"""
        if not GITHUB_TOKEN:
            logger.warning("GitHub token not configured, skipping branch creation")
            return False
            
        try:
            # Get main branch SHA
            main_response = await self.client.get(
                f"{self.base_url}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/refs/heads/main"
            )
            if main_response.status_code != 200:
                logger.error(f"Failed to get main branch: {main_response.text}")
                return False
            
            main_sha = main_response.json()["object"]["sha"]
            
            # Create new branch
            branch_data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": main_sha
            }
            
            branch_response = await self.client.post(
                f"{self.base_url}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/refs",
                json=branch_data
            )
            
            return branch_response.status_code == 201
            
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return False
    
    async def commit_files(self, branch_name: str, files: Dict[str, str], commit_message: str) -> bool:
        """Commit multiple files to branch"""
        if not GITHUB_TOKEN:
            logger.warning("GitHub token not configured, skipping file commit")
            return False
            
        try:
            for file_path, content in files.items():
                await self._create_or_update_file(branch_name, file_path, content, commit_message)
            return True
        except Exception as e:
            logger.error(f"Error committing files: {e}")
            return False
    
    async def _create_or_update_file(self, branch_name: str, file_path: str, content: str, message: str):
        """Create or update a single file"""
        encoded_content = base64.b64encode(content.encode()).decode()
        
        # Check if file exists
        file_response = await self.client.get(
            f"{self.base_url}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{file_path}?ref={branch_name}"
        )
        
        file_data = {
            "message": message,
            "content": encoded_content,
            "branch": branch_name
        }
        
        if file_response.status_code == 200:
            # File exists, update it
            file_data["sha"] = file_response.json()["sha"]
        
        # Create or update file
        await self.client.put(
            f"{self.base_url}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{file_path}",
            json=file_data
        )
    
    async def create_pull_request(self, branch_name: str, title: str, body: str) -> Optional[str]:
        """Create a pull request"""
        if not GITHUB_TOKEN:
            logger.warning("GitHub token not configured, skipping PR creation")
            return None
            
        try:
            pr_data = {
                "title": title,
                "body": body,
                "head": branch_name,
                "base": "main"
            }
            
            pr_response = await self.client.post(
                f"{self.base_url}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/pulls",
                json=pr_data
            )
            
            if pr_response.status_code == 201:
                return pr_response.json()["html_url"]
            else:
                logger.error(f"Failed to create PR: {pr_response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()

class TerraformGenerator:
    """Generates Terraform files from parsed configurations"""
    
    @staticmethod
    def generate_files(config: Dict[str, Any]) -> Dict[str, str]:
        """Generate all necessary Terraform files - Fixed template rendering"""
        files = {}
        
        # Generate provider.tf using string formatting instead of Jinja2
        provider_template = TERRAFORM_TEMPLATES["provider"]
        files["provider.tf"] = provider_template.format(**config)
        
        # Generate main resource file using string formatting instead of Jinja2
        resource_type = config["resource_type"]
        if resource_type in TERRAFORM_TEMPLATES:
            template = TERRAFORM_TEMPLATES[resource_type]
            files["main.tf"] = template.format(**config)
        
        # Generate variables.tf
        files["variables.tf"] = TerraformGenerator._generate_variables(config)
        
        # Generate terraform.tfvars
        files["terraform.tfvars"] = TerraformGenerator._generate_tfvars(config)
        
        # Generate README.md
        files["README.md"] = TerraformGenerator._generate_readme(config)
        
        return files
    
    @staticmethod
    def _generate_variables(config: Dict[str, Any]) -> str:
        """Generate variables.tf file"""
        return f'''# Variables for {config["resource_type"]}
variable "project_id" {{
  description = "GCP Project ID"
  type        = string
  default     = "{config["project_id"]}"
}}

variable "region" {{
  description = "GCP Region"
  type        = string
  default     = "{config["region"]}"
}}

variable "environment" {{
  description = "Environment name"
  type        = string
  default     = "{config["environment"]}"
}}
'''
    
    @staticmethod
    def _generate_tfvars(config: Dict[str, Any]) -> str:
        """Generate terraform.tfvars file"""
        return f'''# Terraform Variables
project_id  = "{config["project_id"]}"
region      = "{config["region"]}"
environment = "{config["environment"]}"
'''
    
    @staticmethod
    def _generate_readme(config: Dict[str, Any]) -> str:
        """Generate README.md file"""
        return f'''# Terraform Infrastructure

Generated by AI Terraform Agent from instruction: "{config.get("instruction", "N/A")}"

## Resources Created

- **Type**: {config["resource_type"]}
- **Environment**: {config["environment"]}
- **Region**: {config["region"]}

## Usage

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the changes
terraform apply

# Destroy resources (when needed)
terraform destroy
```

## Generated Files

- `provider.tf` - Provider configuration
- `main.tf` - Main resource definitions
- `variables.tf` - Variable declarations
- `terraform.tfvars` - Variable values

---
*Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC*
'''

# API Endpoints
@app.post("/terraform/generate", response_model=TerraformResponse)
async def generate_terraform(request: TerraformRequest, background_tasks: BackgroundTasks):
    """Generate Terraform code from natural language instruction"""
    try:
        # Parse instruction
        config = KAgent.parse_instruction(request.instruction)
        
        # Generate Terraform files
        terraform_files = TerraformGenerator.generate_files(config)
        
        # Create branch name
        branch_name = request.branch_name or f"terraform-{config['resource_type']}-{config['timestamp']}"
        
        # Schedule GitHub operations in background (only if configured)
        if GITHUB_TOKEN and GITHUB_OWNER:
            background_tasks.add_task(
                deploy_to_github,
                branch_name,
                terraform_files,
                request.instruction,
                config
            )
            message = "Terraform files generated successfully. GitHub deployment in progress."
        else:
            message = "Terraform files generated successfully. (GitHub not configured)"
        
        return TerraformResponse(
            success=True,
            message=message,
            branch_name=branch_name,
            terraform_files=terraform_files
        )
        
    except Exception as e:
        logger.error(f"Error generating Terraform: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def deploy_to_github(branch_name: str, files: Dict[str, str], instruction: str, config: Dict[str, Any]):
    """Deploy generated files to GitHub and create PR"""
    github_manager = GitHubManager()
    
    try:
        # Create branch
        if not await github_manager.create_branch(branch_name):
            logger.error(f"Failed to create branch: {branch_name}")
            return
        
        # Commit files
        commit_message = f"Add Terraform config: {instruction}"
        if not await github_manager.commit_files(branch_name, files, commit_message):
            logger.error(f"Failed to commit files to branch: {branch_name}")
            return
        
        # Create PR
        pr_title = f"🚀 Terraform: {instruction}"
        pr_body = f"""
## AI-Generated Terraform Configuration

**Instruction**: {instruction}

**Resources Created**:
- Type: {config['resource_type']}
- Environment: {config['environment']}
- Region: {config['region']}

**Files Added**:
{chr(10).join([f"- `{filename}`" for filename in files.keys()])}

---
*This PR was automatically created by the AI Terraform Agent*
        """
        
        pr_url = await github_manager.create_pull_request(branch_name, pr_title, pr_body)
        if pr_url:
            logger.info(f"Created PR: {pr_url}")
        else:
            logger.error("Failed to create pull request")
            
    except Exception as e:
        logger.error(f"Error in GitHub deployment: {e}")
    finally:
        await github_manager.close()

@app.get("/terraform/templates")
async def list_templates():
    """List available Terraform templates"""
    return {
        "templates": list(TERRAFORM_TEMPLATES.keys()),
        "supported_resources": [
            "GCP VM Instances",
            "GCP Storage Buckets", 
            "GCP VPC Networks",
            "Provider Configuration"
        ]
    }

# MCP SSE Endpoints
@app.get("/mcp/events")
async def mcp_events():
    """Server-Sent Events endpoint for MCP compatibility"""
    async def event_stream():
        while True:
            # Send heartbeat
            event = MCPEvent(
                event="heartbeat",
                data={"timestamp": datetime.now().isoformat(), "status": "active"}
            )
            yield f"data: {event.json()}\n\n"
            await asyncio.sleep(30)
    
    return StreamingResponse(event_stream(), media_type="text/plain")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "github_configured": bool(GITHUB_TOKEN and GITHUB_OWNER),
        "gcp_configured": bool(GCP_PROJECT_ID)
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Terraform Agent",
        "version": "1.0.0",
        "description": "Convert natural language to Terraform code and deploy via GitHub PRs",
        "endpoints": {
            "generate": "/terraform/generate",
            "templates": "/terraform/templates", 
            "mcp_events": "/mcp/events",
            "health": "/health"
        },
        "github_repo": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}" if GITHUB_OWNER else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
