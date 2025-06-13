
docs/CONTRIBUTING.md
Contributing to AI Terraform Agent
Welcome!
Thank you for considering contributing to the AI Terraform Agent! This document provides guidelines and information for contributors.
Code of Conduct
This project adheres to a Code of Conduct. By participating, you are expected to uphold this code.
How to Contribute
Reporting Issues

Check existing issues before creating new ones
Use the appropriate issue template
Provide detailed information and steps to reproduce
Include environment information

Submitting Changes

Fork the repository
Create a feature branch: git checkout -b feature/new-feature
Make your changes
Add tests for new functionality
Ensure tests pass: pytest tests/ -v
Submit a pull request

Development Setup
bash# Clone your fork
git clone https://github.com/yourusername/ai-terraform-agent.git

# Setup development environment
./setup.sh --skip-docker

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8

# Run tests
pytest tests/ -v

# Format code
black .
flake8 .
Code Style

Follow PEP 8 style guidelines
Use type hints for all functions
Write comprehensive docstrings
Add unit tests for new features

Commit Guidelines

Use clear, descriptive commit messages
Follow conventional commits format:

feat: for new features
fix: for bug fixes
docs: for documentation
test: for tests
refactor: for refactoring



Testing

Write tests for all new functionality
Maintain test coverage above 80%
Use pytest fixtures for common test data
Mock external API calls

Documentation

Update README.md for user-facing changes
Add docstrings to all functions and classes
Update API documentation for endpoint changes
Include examples for new features
