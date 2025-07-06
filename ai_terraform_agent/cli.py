#!/usr/bin/env python3
"""
CLI Tool for AI Terraform Agent
Provides command-line interface for generating Terraform configurations
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

class TerraformCLI:
    """Command-line interface for the Terraform Agent"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def generate_terraform(self, instruction: str, branch_name: str = None, output_dir: str = None) -> Dict[str, Any]:
        """Generate Terraform configuration from instruction"""
        payload = {
            "instruction": instruction,
            "branch_name": branch_name,
            "auto_merge": False
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/terraform/generate", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                console.print(f"[red]Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            console.print(f"[red]Connection error: {e}")
            return None
    
    async def list_templates(self) -> Dict[str, Any]:
        """List available templates"""
        try:
            response = await self.client.get(f"{self.base_url}/terraform/templates")
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            console.print(f"[red]Error fetching templates: {e}")
            return None
    
    def save_files(self, files: Dict[str, str], output_dir: str = "./terraform_output"):
        """Save generated files to local directory"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        for filename, content in files.items():
            file_path = output_path / filename
            with open(file_path, 'w') as f:
                f.write(content)
            saved_files.append(str(file_path))
        
        return saved_files
    
    def display_files(self, files: Dict[str, str]):
        """Display generated files with syntax highlighting"""
        for filename, content in files.items():
            # Determine syntax based on file extension
            if filename.endswith('.tf'):
                lexer = "hcl"
            elif filename.endswith('.md'):
                lexer = "markdown"
            elif filename.endswith('.tfvars'):
                lexer = "hcl"
            else:
                lexer = "text"
            
            syntax = Syntax(content, lexer, theme="monokai", line_numbers=True)
            panel = Panel(syntax, title=filename, border_style="blue")
            console.print(panel)
            console.print()

async def cmd_generate(args):
    """Generate Terraform configuration"""
    cli = TerraformCLI(args.url)
    
    try:
        # Health check
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Checking service health...", total=None)
            if not await cli.health_check():
                console.print("[red]❌ Service is not available. Make sure the server is running.")
                return 1
            progress.update(task, description="✅ Service is healthy")
        
        # Get instruction
        if args.instruction:
            instruction = args.instruction
        else:
            instruction = Prompt.ask("Enter your Terraform instruction")
        
        if not instruction.strip():
            console.print("[red]❌ Instruction cannot be empty")
            return 1
        
        # Generate Terraform
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Generating Terraform configuration...", total=None)
            result = await cli.generate_terraform(instruction, args.branch, args.output)
            
            if not result or not result.get("success"):
                console.print("[red]❌ Failed to generate Terraform configuration")
                return 1
            
            progress.update(task, description="✅ Terraform configuration generated")
        
        # Display results
        console.print(f"\n[green]✅ Successfully generated Terraform configuration!")
        console.print(f"[blue]Branch: {result.get('branch_name', 'N/A')}")
        console.print(f"[blue]Message: {result.get('message', 'N/A')}")
        
        if result.get("pr_url"):
            console.print(f"[blue]Pull Request: {result['pr_url']}")
        
        # Handle files
        if result.get("terraform_files"):
            files = result["terraform_files"]
            
            if args.output:
                saved_files = cli.save_files(files, args.output)
                console.print(f"\n[green]Files saved to: {args.output}")
                for file_path in saved_files:
                    console.print(f"  📄 {file_path}")
            
            if args.show or not args.output:
                console.print("\n[cyan]Generated Files:")
                cli.display_files(files)
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled")
        return 1
    finally:
        await cli.close()

async def cmd_templates(args):
    """List available templates"""
    cli = TerraformCLI(args.url)
    
    try:
        templates = await cli.list_templates()
        if not templates:
            console.print("[red]❌ Failed to fetch templates")
            return 1
        
        # Create table
        table = Table(title="Available Terraform Templates")
        table.add_column("Template", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        
        template_descriptions = {
            "gcp_vm": "Google Cloud VM instances with customizable specs",
            "gcp_storage": "Google Cloud Storage buckets with versioning",
            "gcp_network": "Google Cloud VPC networks with subnets and firewalls",
            "provider": "Terraform provider configuration for Google Cloud"
        }
        
        for template in templates.get("templates", []):
            description = template_descriptions.get(template, "Terraform resource template")
            table.add_row(template, description)
        
        console.print(table)
        
        if templates.get("supported_resources"):
            console.print("\n[blue]Supported Resources:")
            for resource in templates["supported_resources"]:
                console.print(f"  • {resource}")
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled")
        return 1
    finally:
        await cli.close()

async def cmd_health(args):
    """Check service health"""
    cli = TerraformCLI(args.url)
    
    try:
        if await cli.health_check():
            console.print("[green]✅ Service is healthy and ready")
            return 0
        else:
            console.print("[red]❌ Service is not available")
            return 1
    finally:
        await cli.close()

async def cmd_interactive(args):
    """Interactive mode"""
    cli = TerraformCLI(args.url)
    
    try:
        console.print("[cyan]🤖 AI Terraform Agent - Interactive Mode")
        console.print("Type 'help' for commands, 'quit' to exit\n")
        
        while True:
            try:
                command = Prompt.ask("terraform-agent")
                
                if command.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]👋 Goodbye!")
                    break
                elif command.lower() in ['help', 'h']:
                    console.print("""
[cyan]Available Commands:[/cyan]
  generate <instruction>  - Generate Terraform from natural language
  templates              - List available templates  
  health                 - Check service health
  clear                  - Clear screen
  quit/exit              - Exit interactive mode
  
[cyan]Examples:[/cyan]
  generate Create a small Ubuntu VM named web-server
  generate Create a storage bucket in Europe with versioning
  generate Create a VPC network with firewall rules
                    """)
                elif command.lower() == 'clear':
                    console.clear()
                elif command.lower() == 'templates':
                    await cmd_templates(args)
                elif command.lower() == 'health':
                    await cmd_health(args)
                elif command.lower().startswith('generate '):
                    instruction = command[9:].strip()  # Remove 'generate '
                    if instruction:
                        args.instruction = instruction
                        args.show = True
                        await cmd_generate(args)
                    else:
                        console.print("[red]❌ Please provide an instruction")
                else:
                    console.print("[yellow]⚠️  Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit")
            except EOFError:
                break
        
        return 0
        
    finally:
        await cli.close()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Terraform Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  terraform-cli generate "Create a Ubuntu VM instance"
  terraform-cli generate --output ./my-terraform --branch feature/new-vm "Create a large VM"
  terraform-cli templates
  terraform-cli interactive
        """
    )
    
    parser.add_argument(
        "--url", 
        default="http://localhost:12000",
        help="Base URL of the Terraform Agent service"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate Terraform configuration")
    gen_parser.add_argument("instruction", nargs="?", help="Natural language instruction")
    gen_parser.add_argument("--branch", help="Custom branch name for GitHub")
    gen_parser.add_argument("--output", "-o", help="Output directory for generated files")
    gen_parser.add_argument("--show", "-s", action="store_true", help="Display generated files")
    gen_parser.set_defaults(func=cmd_generate)
    
    # Templates command
    templates_parser = subparsers.add_parser("templates", help="List available templates")
    templates_parser.set_defaults(func=cmd_templates)
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check service health")
    health_parser.set_defaults(func=cmd_health)
    
    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode")
    interactive_parser.set_defaults(func=cmd_interactive)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run the async command
    try:
        return asyncio.run(args.func(args))
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
