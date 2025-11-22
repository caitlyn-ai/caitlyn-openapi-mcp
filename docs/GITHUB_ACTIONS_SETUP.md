# GitHub Actions CI/CD Setup Guide

## Overview

This project uses GitHub Actions for continuous integration and deployment. The workflow automatically:

- Runs linting and tests on all PRs
- Builds and pushes Docker images to ECR
- Publishes to PyPI on tagged releases
- Creates GitHub releases with changelogs

## Required Secrets and Configuration

### 1. AWS OIDC Setup (Recommended - No Long-lived Credentials!)

GitHub Actions uses OpenID Connect (OIDC) to authenticate with AWS without storing long-lived credentials.

#### Create IAM OIDC Provider in AWS:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

#### Create IAM Role for GitHub Actions:

1. Create trust policy (`github-actions-trust-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::011528297224:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:caitlyn-ai/caitlyn-openapi-mcp:*"
        }
      }
    }
  ]
}
```

2. Create the role:

```bash
aws iam create-role \
  --role-name GitHubActions-CaitlynOpenAPIMCP \
  --assume-role-policy-document file://github-actions-trust-policy.json
```

3. Attach ECR permissions policy (`ecr-permissions.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeImages"
      ],
      "Resource": "arn:aws:ecr:ap-southeast-2:011528297224:repository/caitlyn/mcp/openapi"
    },
    {
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["ecr-public:GetAuthorizationToken", "sts:GetServiceBearerToken"],
      "Resource": "*"
    }
  ]
}
```

4. Attach the policy:

```bash
aws iam put-role-policy \
  --role-name GitHubActions-CaitlynOpenAPIMCP \
  --policy-name ECRAccess \
  --policy-document file://ecr-permissions.json
```

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions → Repository secrets**

#### Required Secret:

**`AWS_ROLE_ARN`**

- Value: `arn:aws:iam::011528297224:role/GitHubActions-CaitlynOpenAPIMCP`
- Description: IAM role ARN for OIDC authentication with AWS

### 3. Configure PyPI Trusted Publishing (No Token Needed!)

GitHub Actions can publish to PyPI using trusted publishing without storing credentials:

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in:
   - **PyPI Project Name**: `caitlyn-openapi-mcp`
   - **Owner**: `caitlyn-ai`
   - **Repository name**: `caitlyn-openapi-mcp`
   - **Workflow name**: `ci.yml`
   - **Environment name**: `pypi`
4. Click "Add"

That's it! No API tokens needed for PyPI publishing.

### 4. Optional: Codecov Integration

For code coverage reporting:

1. Sign up at https://codecov.io with your GitHub account
2. Enable the repository
3. No secrets needed - Codecov automatically detects GitHub Actions

## Workflow Jobs

### On Every Push/PR:

1. **Lint** - Code quality checks

   - Black formatting
   - Ruff linting
   - Pyright type checking

2. **Test** - Unit tests
   - Runs pytest with coverage
   - Uploads coverage to Codecov

### On Push to Main:

3. **Build Package** - Python wheel and sdist
4. **Build Docker** - ARM64 image pushed to ECR
5. **Security Scan** - Trivy vulnerability scanning
   - Results uploaded to GitHub Security tab

### On Git Tags (v\*):

6. **Publish to PyPI** - Automatic via trusted publishing
7. **Tag Docker as Stable** - Creates `stable` and version tags
8. **Create GitHub Release** - Automatic release with changelog

## Creating a Release

1. **Update version** in `pyproject.toml`:

   ```toml
   version = "0.4.0"
   ```

2. **Commit and push**:

   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.4.0"
   git push origin main
   ```

3. **Create and push tag**:

   ```bash
   git tag v0.4.0
   git push origin v0.4.0
   ```

4. **Automated actions**:
   - ✅ Package published to PyPI
   - ✅ Docker image tagged as `v0.4.0` and `stable`
   - ✅ GitHub Release created with changelog
   - ✅ Distribution files attached to release

## Workflow Triggers

- **Pull Requests**: Runs lint and test only
- **Push to main**: Runs all jobs except publish
- **Tags (v\*)**: Runs complete pipeline including publish
- **Manual**: Can be triggered via "Run workflow" button

## Monitoring

### GitHub Actions UI

- View all workflow runs: **Actions** tab
- Check job logs and artifacts
- Download build artifacts

### GitHub Security

- View vulnerability scans: **Security → Code scanning**
- Trivy results appear here automatically

### Codecov

- View coverage reports: https://codecov.io/gh/caitlyn-ai/caitlyn-openapi-mcp
- PR comments with coverage changes

## Environment Protection (Optional)

For extra safety on PyPI publishing:

1. Go to **Settings → Environments**
2. Create environment named `pypi`
3. Add protection rules:
   - Required reviewers (optional)
   - Wait timer (optional)
   - Deployment branches: `refs/tags/v*`

## Local Testing

Test the workflow locally before pushing:

```bash
# Install act (GitHub Actions local runner)
brew install act

# Run the workflow
act push

# Run specific job
act -j test
```

## Troubleshooting

### Docker build fails

- Check AWS role ARN is correct
- Verify IAM role has ECR permissions
- Check OIDC provider is configured

### PyPI publish fails

- Verify trusted publisher is configured on PyPI
- Check repository name matches exactly
- Ensure tag starts with `v` (e.g., `v0.3.0`)

### Security scan fails

- This job is allowed to fail
- Check the Security tab for detailed results
- HIGH/CRITICAL vulnerabilities are flagged

## Advantages over GitLab CI/CD

✅ **Native to GitHub** - Better integration with PRs and releases
✅ **No token management** - OIDC for AWS, trusted publishing for PyPI
✅ **Free for public repos** - Unlimited minutes
✅ **Better visibility** - Security tab, Codecov integration
✅ **Community actions** - Extensive marketplace
✅ **Automatic releases** - Changelog generation from commits
