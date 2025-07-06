#!/usr/bin/env python3
"""
AI-Assisted Terraform Agent
A FastAPI-based service that converts natural language to Terraform code,
pushes to GitHub, and creates Pull Requests.

This is a wrapper script that imports from the ai_terraform_agent package.
"""

import logging
from ai_terraform_agent.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
