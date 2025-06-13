
#!/usr/bin/env python3
# tools/migration-helper.py
"""
Migration Helper Tool
Helps migrate existing Terraform configurations to AI Agent format
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import hcl2

class MigrationHelper:
    def __init__(self):
        self.supported_resources = {
            "google_compute_instance": "gcp_vm",
            "google_storage_bucket": "gcp_storage", 
            "google_compute_network": "gcp_network",
            "google_compute_subnetwork": "gcp_network"
        }
    
    def analyze_terraform_files(self, terraform_dir: str) -> Dict[str, Any]:
        """Analyze existing Terraform files"""
        terraform_path = Path(terraform_dir)
        analysis = {
            "files": [],
            "resources": [],
            "providers": [],
            "variables": [],
            "outputs": [],
            "migration_suggestions": []
        }
        
        # Find all .tf files
        tf_files = list(terraform_path.glob("*.tf"))
        
        for tf_file in tf_files:
            print(f"Analyzing {tf_file}...")
            file_analysis = self._analyze_file(tf_file)
            analysis["files"].append({
                "path": str(tf_file),
                "analysis": file_analysis
            })
            
            # Aggregate resources, providers, etc.
            analysis["resources"].extend(file_analysis.get("resources", []))
            analysis["providers"].extend(file_analysis.get("providers", []))
            analysis["variables"].extend(file_analysis.get("variables", []))
            analysis["outputs"].extend(file_analysis.get("outputs", []))
        
        # Generate migration suggestions
        analysis["migration_suggestions"] = self._generate_migration_suggestions(analysis)
        
        return analysis
    
    def _analyze_file(self, tf_file: Path) -> Dict[str, Any]:
        """Analyze a single Terraform file"""
        analysis = {
            "resources": [],
            "providers": [],
            "variables": [],
            "outputs": []
        }
        
        try:
            with open(tf_file, 'r') as f:
                content = f.read()
            
            # Try to parse with python-hcl2
            try:
                parsed = hcl2.loads(content)
                analysis = self._extract_from_parsed(parsed)
            except Exception:
                # Fallback to regex parsing
                analysis = self._extract_with_regex(content)
                
        except Exception as e:
            print(f"Error analyzing {tf_file}: {e}")
        
        return analysis
    
    def _extract_from_parsed(self, parsed: Dict) -> Dict[str, Any]:
        """Extract information from parsed HCL"""
        analysis = {
            "resources": [],
            "providers": [],
            "variables": [],
            "outputs": []
        }
        
        # Extract resources
        if "resource" in parsed:
            for resource_type, resources in parsed["resource"].items():
                for resource_name, resource_config in resources.items():
                    analysis["resources"].append({
                        "type": resource_type,
                        "name": resource_name,
                        "config": resource_config,
                        "ai_agent_compatible": resource_type in self.supported_resources
                    })
        
        # Extract providers
        if "provider" in parsed:
            for provider_name, provider_config in parsed["provider"].items():
                analysis["providers"].append({
                    "name": provider_name,
                    "config": provider_config
                })
        
        # Extract variables
        if "variable" in parsed:
            for var_name, var_config in parsed["variable"].items():
                analysis["variables"].append({
                    "name": var_name,
                    "config": var_config
                })
        
        # Extract outputs  
        if "output" in parsed:
            for output_name, output_config in parsed["output"].items():
                analysis["outputs"].append({
                    "name": output_name,
                    "config": output_config
                })
        
        return analysis
    
    def _extract_with_regex(self, content: str) -> Dict[str, Any]:
        """Extract information using regex (fallback method)"""
        analysis = {
            "resources": [],
            "providers": [],
            "variables": [],
            "outputs": []
        }
        
        # Extract resources
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*{'
        for match in re.finditer(resource_pattern, content):
            resource_type, resource_name = match.groups()
            analysis["resources"].append({
                "type": resource_type,
                "name": resource_name,
                "ai_agent_compatible": resource_type in self.supported_resources
            })
        
        # Extract providers
        provider_pattern = r'provider\s+"([^"]+)"\s*{'
        for match in re.finditer(provider_pattern, content):
            provider_name = match.group(1)
            analysis["providers"].append({"name": provider_name})
        
        return analysis
    
    def _generate_migration_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate migration suggestions based on analysis"""
        suggestions = []
        
        # Check for supported resources
        supported_count = sum(1 for r in analysis["resources"] if r.get("ai_agent_compatible", False))
        total_count = len(analysis["resources"])
        
        if supported_count > 0:
            suggestions.append(f"✅ {supported_count}/{total_count} resources are compatible with AI Terraform Agent")
        
        if supported_count < total_count:
            unsupported = [r["type"] for r in analysis["resources"] if not r.get("ai_agent_compatible", False)]
            unique_unsupported = list(set(unsupported))
            suggestions.append(f"⚠️  Unsupported resource types: {', '.join(unique_unsupported)}")
        
        # Check for provider compatibility
        google_providers = [p for p in analysis["providers"] if p["name"] == "google"]
        if google_providers:
            suggestions.append("✅ Google Cloud provider detected - compatible with AI Agent")
        
        # Suggest migration steps
        if supported_count > 0:
            suggestions.append("💡 Migration steps:")
            suggestions.append("   1. Backup existing Terraform state")
            suggestions.append("   2. Generate equivalent configurations using AI Agent")
            suggestions.append("   3. Import existing resources to new state")
            suggestions.append("   4. Validate and test new configurations")
        
        return suggestions
    
    def generate_migration_commands(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate terraform import commands for migration"""
        commands = ['# Terraform import commands for migration', '']
        
        for resource in analysis["resources"]:
            if resource.get("ai_agent_compatible", False):
                resource_type = resource["type"]
                resource_name = resource["name"]
                
                if resource_type == "google_compute_instance":
                    commands.append(f"# Import VM instance: {resource_name}")
                    commands.append(f"terraform import {resource_type}.{resource_name} projects/PROJECT_ID/zones/ZONE/instances/{resource_name}")
                    commands.append("")
                
                elif resource_type == "google_storage_bucket":
                    commands.append(f"# Import storage bucket: {resource_name}")
                    commands.append(f"terraform import {resource_type}.{resource_name} {resource_name}")
                    commands.append("")
                
                elif resource_type == "google_compute_network":
                    commands.append(f"# Import VPC network: {resource_name}")
                    commands.append(f"terraform import {resource_type}.{resource_name} projects/PROJECT_ID/global/networks/{resource_name}")
                    commands.append("")
        
        return commands
    
    def generate_ai_instructions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate AI Agent instructions based on existing resources"""
        instructions = []
        
        for resource in analysis["resources"]:
            if not resource.get("ai_agent_compatible", False):
                continue
                
            resource_type = resource["type"]
            resource_name = resource["name"]
            config = resource.get("config", {})
            
            if resource_type == "google_compute_instance":
                machine_type = config.get("machine_type", "e2-micro")
                size = "small" if "micro" in machine_type else "medium" if "standard-2" in machine_type else "large"
                
                instruction = f"Create a {size} VM instance named {resource_name}"
                if "ubuntu" in str(config).lower():
                    instruction += " with Ubuntu"
                elif "centos" in str(config).lower():
                    instruction += " with CentOS"
                
                instructions.append(instruction)
            
            elif resource_type == "google_storage_bucket":
                instruction = f"Create a storage bucket named {resource_name}"
                if config.get("location") == "EU":
                    instruction += " in Europe"
                elif config.get("location") == "ASIA":
                    instruction += " in Asia"
                
                if config.get("versioning", {}).get("enabled"):
                    instruction += " with versioning"
                
                instructions.append(instruction)
            
            elif resource_type == "google_compute_network":
                instruction = f"Create a VPC network named {resource_name}"
                instructions.append(instruction)
        
        return instructions

def main():
    parser = argparse.ArgumentParser(description="Migration helper for Terraform to AI Agent")
    parser.add_argument(
        "terraform_dir",
        help="Directory containing existing Terraform files"
    )
    parser.add_argument(
        "--output",
        default="migration-analysis.json",
        help="Output file for analysis results"
    )
    parser.add_argument(
        "--generate-commands",
        action="store_true",
        help="Generate terraform import commands"
    )
    parser.add_argument(
        "--generate-instructions",
        action="store_true", 
        help="Generate AI Agent instructions"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.terraform_dir):
        print(f"❌ Directory {args.terraform_dir} does not exist")
        return 1
    
    helper = MigrationHelper()
    
    print(f"🔍 Analyzing Terraform files in {args.terraform_dir}...")
    analysis = helper.analyze_terraform_files(args.terraform_dir)
    
    # Save analysis
    with open(args.output, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"📊 Analysis saved to {args.output}")
    
    # Print summary
    print("\n" + "="*50)
    print("MIGRATION ANALYSIS SUMMARY")
    print("="*50)
    
    print(f"Files analyzed: {len(analysis['files'])}")
    print(f"Resources found: {len(analysis['resources'])}")
    print(f"Providers found: {len(analysis['providers'])}")
    
    print("\n📋 Migration Suggestions:")
    for suggestion in analysis['migration_suggestions']:
        print(f"  {suggestion}")
    
    # Generate additional outputs
    if args.generate_commands:
        commands = helper.generate_migration_commands(analysis)
        commands_file = "migration-commands.sh"
        with open(commands_file, 'w') as f:
            f.write('\n'.join(commands))
        print(f"\n💻 Import commands saved to {commands_file}")
    
    if args.generate_instructions:
        instructions = helper.generate_ai_instructions(analysis)
        instructions_file = "ai-instructions.txt"
        with open(instructions_file, 'w') as f:
            f.write('# AI Agent Instructions\n\n')
            for i, instruction in enumerate(instructions, 1):
                f.write(f"{i}. {instruction}\n")
        print(f"\n🤖 AI instructions saved to {instructions_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())
