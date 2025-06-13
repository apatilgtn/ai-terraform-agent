
# tests/fixtures/mock_responses.py
"""Mock API responses for testing."""

GITHUB_MAIN_BRANCH_RESPONSE = {
    "object": {
        "sha": "d6fde92930d4715a2b49857d24b940956b26d2d3",
        "type": "commit",
        "url": "https://api.github.com/repos/test/repo/git/commits/d6fde92930d4715a2b49857d24b940956b26d2d3"
    }
}

GITHUB_CREATE_BRANCH_RESPONSE = {
    "ref": "refs/heads/feature/new-vm",
    "node_id": "MDM6UmVmcmVmcmVmcw==",
    "url": "https://api.github.com/repos/test/repo/git/refs/heads/feature/new-vm",
    "object": {
        "sha": "d6fde92930d4715a2b49857d24b940956b26d2d3",
        "type": "commit",
        "url": "https://api.github.com/repos/test/repo/git/commits/d6fde92930d4715a2b49857d24b940956b26d2d3"
    }
}

GITHUB_CREATE_PR_RESPONSE = {
    "id": 1,
    "number": 1,
    "state": "open",
    "title": "Add new VM configuration",
    "body": "Automated PR from Terraform Agent",
    "html_url": "https://github.com/test/repo/pull/1",
    "user": {
        "login": "test-user"
    },
    "head": {
        "ref": "feature/new-vm"
    },
    "base": {
        "ref": "main"  
    }
}

GCP_REGIONS_RESPONSE = [
    "us-central1",
    "us-east1", 
    "us-west1",
    "europe-west1",
    "asia-southeast1"
]
