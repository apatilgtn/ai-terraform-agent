#!/usr/bin/env python3
"""
CLI Tool for AI Terraform Agent
Provides command-line interface for generating Terraform configurations

This is a wrapper script that imports from the ai_terraform_agent package.
"""

import sys
from ai_terraform_agent.cli import main

if __name__ == "__main__":
    sys.exit(main())
