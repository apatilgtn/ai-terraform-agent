
Troubleshooting Guide
Common Issues
GitHub Authentication Failed
Symptoms: 401/403 errors when creating branches or PRs
Solutions:

Verify GitHub token has correct permissions
Check token hasn't expired
Ensure repository exists and is accessible

bash# Test GitHub access
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
GCP Permission Denied
Symptoms: GCP API errors when generating Terraform
Solutions:

Verify GCP project ID is correct
Check if required APIs are enabled
Ensure proper authentication

bash# Test GCP access
gcloud auth application-default print-access-token
gcloud compute instances list --project=$GCP_PROJECT_ID
Service Unavailable
Symptoms: CLI health check fails
Solutions:

Check if service is running
Verify port 8000 is accessible
Check Docker/Kubernetes logs

bash# Check service status
./terraform-cli health

# Check Docker logs
docker-compose logs terraform-agent

# Check Kubernetes logs
kubectl logs -n terraform-agent deployment/terraform-agent
Terraform Validation Errors
Symptoms: Generated Terraform files fail validation
Solutions:

Check Terraform syntax
Verify provider configuration
Validate resource parameters

bash# Validate Terraform
cd terraform_output
terraform init
terraform validate
terraform plan
Debug Mode
Enable debug logging:
bashexport LOG_LEVEL=DEBUG
./start.sh
Getting Help

Check this troubleshooting guide
Search existing GitHub issues
Create a new issue with detailed information
Join our community discussions
