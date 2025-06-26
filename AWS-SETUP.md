# AWS Free Tier Setup for Airspace Viewer

Deploy the Airspace Viewer application to AWS using **Free Tier eligible** resources ($0 cost for 12 months).

## 📋 Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **AWS Administrator Access** - You need an account or IAM user with `AdministratorAccess` policy
3. **AWS CLI** installed and configured with admin credentials

### Create Admin User

You must have AWS Administrator access to create the deployment user and resources. This can be:

- Your root AWS account (not recommended for daily use)
- An IAM user with the `AdministratorAccess` policy attached

#### If you need to create an admin user

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click "Users" in the left sidebar
3. Click "Create user"
4. Enter username: `admin`
5. Select "Provide user access to the AWS Management Console" (optional)
6. Select "I want to create an IAM user"
7. Click "Next"
8. Click "Attach policies directly" and select:
   - `AdministratorAccess`
9. Click "Next" through remaining steps and "Create user"
10. Go to "Security credentials" tab and create access keys for CLI access

### Install AWS CLI

```bash
# Install AWS CLI
# https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

# verify installation
aws --version

# Configure with admin credentials
aws configure
# Enter your AWS Administrator Access Key ID
# Enter your AWS Administrator Secret Access Key
# Enter your preferred region (e.g., eu-west-1)
# Enter output format (json)
```

**Note**: You'll use the deployment user credentials later for GitHub Actions, but the setup script needs admin access to create resources.

### Create Deployment User

```bash
chmod +x setup-aws-user.sh
./setup-aws-user.sh
```

Save the displayed credentials for GitHub Secrets.

## 🚀 Deployment

```bash
# Run setup script
chmod +x aws-setup.sh
./aws-setup.sh

# Configure GitHub Secrets (use deployment user credentials)
# Copy from .secrets/github-secrets.txt to GitHub: Settings → Secrets → Actions
```

## 🔧 What Gets Created

- **S3 Bucket**: For deployment artifacts
- **Elastic Beanstalk**: Application and environment (t2.micro, single instance)
- **IAM User/Group**: For deployment with minimal required permissions
