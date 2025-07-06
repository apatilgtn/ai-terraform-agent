#!/usr/bin/env python3
"""
Setup configuration for AI Terraform Agent
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read version
def read_version():
    version_file = os.path.join(os.path.dirname(__file__), "VERSION")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    return "1.0.0"

setup(
    name="ai-terraform-agent",
    version=read_version(),
    author="AI Terraform Team",
    author_email="terraform-agent@example.com",
    description="AI-powered Terraform agent that converts natural language to infrastructure code",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/apatilgtn/ai-terraform-agent",
    project_urls={
        "Bug Reports": "https://github.com/apatilgtn/ai-terraform-agent/issues",
        "Documentation": "https://github.com/apatilgtn/ai-terraform-agent/docs",
        "Source": "https://github.com/apatilgtn/ai-terraform-agent",
    },
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.5.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "structlog>=23.2.0",
        ],
        "enhanced-ai": [
            "openai>=1.3.0",
            "anthropic>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "terraform-agent=ai_terraform_agent.main:main",
            "terraform-cli=ai_terraform_agent.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yml", "*.yaml", "*.json"],
    },
    keywords=[
        "terraform",
        "infrastructure-as-code",
        "ai",
        "natural-language-processing", 
        "devops",
        "cloud-infrastructure",
        "automation",
        "github",
        "fastapi",
    ],
    zip_safe=False,
)
