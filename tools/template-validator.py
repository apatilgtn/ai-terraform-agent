
#!/usr/bin/env python3
# tools/template-validator.py
"""
Template Validator Tool
Validates Terraform templates for syntax and best practices
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import subprocess
import jinja2
from jinja2 import Environment, FileSystemLoader, meta

class TemplateValidator:
    def __init__(self, template_dir: str = "terraform-templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.issues = []
    
    def validate_all_templates(self) -> bool:
        """Validate all templates in the directory"""
        success = True
        
        for template_file in self.template_dir.rglob("*.tf.j2"):
            print(f"Validating {template_file}...")
            if not self.validate_template(template_file):
                success = False
        
        return success
    
    def validate_template(self, template_path: Path) -> bool:
        """Validate a single template"""
        try:
            # Load template
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Parse template
            template = self.env.from_string(template_content)
            
            # Get template variables
            ast = self.env.parse(template_content)
            variables = meta.find_undeclared_variables(ast)
            
            # Validate syntax
            self._validate_jinja_syntax(template_path, template_content)
            
            # Validate terraform syntax with sample values
            self._validate_terraform_syntax(template_path, template, variables)
            
            # Validate best practices
            self._validate_best_practices(template_path, template_content)
            
            print(f"✅ {template_path} validation passed")
            return True
            
        except Exception as e:
            print(f"❌ {template_path} validation failed: {e}")
            self.issues.append(f"{template_path}: {e}")
            return False
    
    def _validate_jinja_syntax(self, template_path: Path, content: str):
        """Validate Jinja2 template syntax"""
        try:
            self.env.from_string(content)
        except jinja2.TemplateSyntaxError as e:
            raise ValueError(f"Jinja2 syntax error: {e}")
    
    def _validate_terraform_syntax(self, template_path: Path, template: jinja2.Template, variables: set):
        """Validate Terraform syntax with sample values"""
        # Create sample values for template variables
        sample_values = self._get_sample_values(variables)
        
        try:
            # Render template with sample values
            rendered_content = template.render(**sample_values)
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as tmp_file:
                tmp_file.write(rendered_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Create temporary directory for terraform init
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tf_file = Path(tmp_dir) / "main.tf"
                    tf_file.write_text(rendered_content)
                    
                    # Run terraform validate
                    result = subprocess.run(
                        ["terraform", "validate"],
                        cwd=tmp_dir,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        raise ValueError(f"Terraform validation failed: {result.stderr}")
            
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
        except subprocess.FileNotFoundError:
            print("⚠️  Terraform not found - skipping syntax validation")
    
    def _validate_best_practices(self, template_path: Path, content: str):
        """Validate Terraform best practices"""
        issues = []
        
        # Check for required elements
        if "output" not in content:
            issues.append("Template should include output values")
        
        if "labels" not in content and "tags" not in content:
            issues.append("Resources should include labels/tags for organization")
        
        if "description" not in content:
            issues.append("Resources should include descriptions")
        
        # Check for security best practices
        if "0.0.0.0/0" in content and "ingress" in content.lower():
            issues.append("Avoid using 0.0.0.0/0 in ingress rules - be more specific")
        
        # Check for hardcoded values
        suspicious_patterns = ["password", "secret", "key", "token"]
        for pattern in suspicious_patterns:
            if f'"{pattern}"' in content.lower():
                issues.append(f"Potential hardcoded {pattern} - use variables instead")
        
        if issues:
            raise ValueError(f"Best practice violations: {'; '.join(issues)}")
    
    def _get_sample_values(self, variables: set) -> Dict[str, Any]:
        """Generate sample values for template variables"""
        sample_values = {
            # Common template variables
            "resource_name": "test_resource",
            "resource_type": "gcp_vm",
            "project_id": "test-project-123456",
            "region": "us-central1",
            "zone": "us-central1-a",
            "environment": "test",
            "timestamp": "20240101120000",
            "instruction": "Test instruction",
            
            # VM specific
            "instance_name": "test-instance",
            "machine_type": "e2-micro",
            "image": "debian-cloud/debian-11",
            "disk_size": 20,
            "metadata": 'startup-script = "echo hello"',
            "tags": '["test"]',
            
            # Storage specific
            "bucket_name": "test-bucket-123456",
            "location": "US",
            "versioning": "false",
            
            # Network specific
            "network_name": "test-network",
            "auto_create_subnets": "false",
            "cidr_range": "10.0.0.0/24",
            "allowed_ports": '["22", "80"]',
            "source_ranges": '["10.0.0.0/8"]',
            "target_tags": '["web"]'
        }
        
        # Add any missing variables with default values
        for var in variables:
            if var not in sample_values:
                sample_values[var] = f"test_{var}"
        
        return sample_values
    
    def generate_report(self) -> str:
        """Generate validation report"""
        if not self.issues:
            return "✅ All templates passed validation!"
        
        report = f"❌ Found {len(self.issues)} validation issues:\n\n"
        for issue in self.issues:
            report += f"- {issue}\n"
        
        return report

def main():
    parser = argparse.ArgumentParser(description="Validate Terraform templates")
    parser.add_argument(
        "--template-dir", 
        default="terraform-templates",
        help="Directory containing template files"
    )
    parser.add_argument(
        "--template",
        help="Specific template file to validate"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed report"
    )
    
    args = parser.parse_args()
    
    validator = TemplateValidator(args.template_dir)
    
    if args.template:
        # Validate specific template
        template_path = Path(args.template)
        success = validator.validate_template(template_path)
    else:
        # Validate all templates
        success = validator.validate_all_templates()
    
    if args.report:
        print("\n" + "="*50)
        print("VALIDATION REPORT")
        print("="*50)
        print(validator.generate_report())
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
