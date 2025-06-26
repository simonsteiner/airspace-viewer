# AWS Free Tier Setup for Airspace Viewer

Deploy the Airspace Viewer application to AWS using **Free Tier eligible** resources ($0 cost for 12 months).

## 📋 Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** installed: [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. **Administrator Access** - IAM user with `AdministratorAccess` policy

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

## 🛠️ Scripts Overview

| Script | Purpose | Requirements |
|--------|---------|--------------|
| `setup-aws-user.sh` | Create deployment user | Admin access |
| `aws-setup.sh` | Create AWS resources | Admin access |
| `check-aws-resources.sh` | Check/manage resources | Any access |

## 🚀 Setup Steps

### 1. Create Deployment User

```bash
chmod +x setup-aws-user.sh
./setup-aws-user.sh
```

Creates IAM user with minimal permissions and saves credentials to `.secrets/deployment-credentials.txt`.

### 2. Create AWS Resources

```bash
chmod +x aws-setup.sh
./aws-setup.sh
```

Creates Free Tier infrastructure:

- S3 bucket for deployments
- Elastic Beanstalk app (t2.micro, single instance)
- GitHub secrets configuration in `.secrets/github-secrets.txt`

### 3. Configure GitHub Actions

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

- `AWS_ACCESS_KEY_ID` (from deployment user)
- `AWS_SECRET_ACCESS_KEY` (from deployment user)
- `FLASK_SECRET_KEY` (generated automatically)

## 🔍 Management

```bash
chmod +x check-aws-resources.sh

# Check status
./check-aws-resources.sh

# List all environments
./check-aws-resources.sh list

# Clean up terminated environments
./check-aws-resources.sh cleanup
```

## 💡 Free Tier Limits

- **EC2**: 750 hours/month of t2.micro instances
- **S3**: 5GB storage
- **Elastic Beanstalk**: No additional charges
