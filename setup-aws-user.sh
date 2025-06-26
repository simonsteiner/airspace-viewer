#!/bin/bash

# AWS User and Group Setup Script for Airspace Viewer
# This script creates a deployment user and group with required permissions
# Requires AWS Administrator access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
GROUP_NAME="airspace-viewer-deployment-group"
USER_NAME="airspace-viewer-deploy-user"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        echo "Installation instructions: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    print_success "AWS CLI is installed"
}

# Function to check if user has admin access
check_admin_access() {
    print_status "Checking AWS credentials and admin access..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured or credentials are invalid."
        echo "Please run 'aws configure' first with your administrator credentials."
        exit 1
    fi
    
    # Test admin access by trying to list IAM users
    if ! aws iam list-users --max-items 1 &> /dev/null; then
        print_error "Current AWS credentials do not have sufficient IAM permissions."
        echo "You need an account with AdministratorAccess policy."
        exit 1
    fi
    
    local current_user=$(aws sts get-caller-identity --query 'Arn' --output text)
    print_success "Authenticated as: $current_user"
}

# Function to create IAM group
create_iam_group() {
    print_status "Creating IAM group: $GROUP_NAME"
    
    # Check if group already exists
    if aws iam get-group --group-name "$GROUP_NAME" &> /dev/null; then
        print_warning "Group $GROUP_NAME already exists"
        return 0
    fi
    
    # Create the group
    aws iam create-group --group-name "$GROUP_NAME"
    print_success "Created group: $GROUP_NAME"
    
    # Attach required policies
    print_status "Attaching policies to group..."
    
    aws iam attach-group-policy \
        --group-name "$GROUP_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonS3FullAccess"
    print_success "Attached AmazonS3FullAccess policy"
    
    aws iam attach-group-policy \
        --group-name "$GROUP_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AdministratorAccess-AWSElasticBeanstalk"
    print_success "Attached AdministratorAccess-AWSElasticBeanstalk policy"
    
    print_success "Group $GROUP_NAME created with required policies"
}

# Function to create IAM user
create_iam_user() {
    print_status "Creating IAM user: $USER_NAME"
    
    # Check if user already exists
    if aws iam get-user --user-name "$USER_NAME" &> /dev/null; then
        print_warning "User $USER_NAME already exists"
        
        # Ensure user is in the group
        if aws iam list-groups-for-user --user-name "$USER_NAME" --query "Groups[?GroupName=='$GROUP_NAME']" --output text | grep -q "$GROUP_NAME"; then
            print_success "User is already in group $GROUP_NAME"
        else
            print_status "Adding user to group $GROUP_NAME"
            aws iam add-user-to-group --group-name "$GROUP_NAME" --user-name "$USER_NAME"
            print_success "Added user to group"
        fi
        return 0
    fi
    
    # Create the user
    aws iam create-user \
        --user-name "$USER_NAME" \
        --tags Key=Purpose,Value=GitHubActionsDeployment Key=Project,Value=AirspaceViewer
    print_success "Created user: $USER_NAME"
    
    # Add user to group
    aws iam add-user-to-group --group-name "$GROUP_NAME" --user-name "$USER_NAME"
    print_success "Added user to group: $GROUP_NAME"
}

# Function to create access keys
create_access_keys() {
    print_status "Creating access keys for user: $USER_NAME"
    
    # Check if user already has access keys
    local existing_keys=$(aws iam list-access-keys --user-name "$USER_NAME" --query 'AccessKeyMetadata[].AccessKeyId' --output text)
    if [ -n "$existing_keys" ]; then
        print_warning "User $USER_NAME already has access keys:"
        echo "$existing_keys"
        read -p "Create new access keys anyway? (y/N): " create_new
        if [[ ! $create_new =~ ^[Yy]$ ]]; then
            print_status "Skipping access key creation"
            return 0
        fi
    fi
    
    # Create access keys
    local credentials=$(aws iam create-access-key --user-name "$USER_NAME" --output json)
    local access_key=$(echo "$credentials" | jq -r '.AccessKey.AccessKeyId')
    local secret_key=$(echo "$credentials" | jq -r '.AccessKey.SecretAccessKey')
    
    print_success "Access keys created for user: $USER_NAME"
    echo ""
    echo "========================================"
    echo "SAVE THESE CREDENTIALS SECURELY!"
    echo "========================================"
    echo "Access Key ID: $access_key"
    echo "Secret Access Key: $secret_key"
    echo "========================================"
    echo ""
    print_warning "These credentials will not be shown again!"
    
    # Save to file
    cat > .secrets/deployment-credentials.txt << EOF
# AWS Deployment User Credentials
# Created: $(date)
# User: $USER_NAME
# Group: $GROUP_NAME

AWS_ACCESS_KEY_ID=$access_key
AWS_SECRET_ACCESS_KEY=$secret_key

# Use these credentials for:
# 1. GitHub Actions secrets (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)
# 2. Local development (if needed)

# Policies attached via group:
# - AmazonS3FullAccess
# - AdministratorAccess-AWSElasticBeanstalk
EOF
    
    print_success "Credentials saved to: .secrets/deployment-credentials.txt"
    print_warning "Keep this file secure and add it to .gitignore"
}

# Function to verify setup
verify_setup() {
    print_status "Verifying setup..."
    
    # Check group exists and has policies
    local group_policies=$(aws iam list-attached-group-policies --group-name "$GROUP_NAME" --query 'AttachedPolicies[].PolicyName' --output text)
    print_success "Group $GROUP_NAME has policies: $group_policies"
    
    # Check user exists and is in group
    local user_groups=$(aws iam list-groups-for-user --user-name "$USER_NAME" --query 'Groups[].GroupName' --output text)
    print_success "User $USER_NAME is in groups: $user_groups"
    
    print_success "Setup verification completed!"
}

# Main function
main() {
    echo "=========================================="
    echo "AWS User and Group Setup for Airspace Viewer"
    echo "=========================================="
    echo ""
    echo "This script will create:"
    echo "  • Group: $GROUP_NAME"
    echo "  • User: $USER_NAME"
    echo "  • Access keys for deployment"
    echo ""
    
    # Check prerequisites
    check_aws_cli
    check_admin_access
    
    echo ""
    read -p "Continue with setup? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_error "Setup cancelled"
        exit 1
    fi
    
    echo ""
    print_status "Starting AWS user and group creation..."
    
    # Create resources
    create_iam_group
    create_iam_user
    
    # Check if jq is available for access key creation
    if command -v jq &> /dev/null; then
        echo ""
        read -p "Create access keys for deployment? (Y/n): " create_keys
        if [[ ! $create_keys =~ ^[Nn]$ ]]; then
            create_access_keys
        fi
    else
        print_warning "jq is not installed. Skipping automatic access key creation."
        print_status "You can create access keys manually in the AWS Console:"
        echo "1. Go to IAM → Users → $USER_NAME → Security credentials"
        echo "2. Click 'Create access key'"
        echo "3. Select 'Command Line Interface (CLI)'"
        echo "4. Save the credentials for GitHub Actions"
    fi
    
    echo ""
    verify_setup
    
    echo ""
    print_success "AWS user and group setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Use the created credentials for GitHub Actions secrets"
    echo "2. Run the main setup script: ./aws-setup.sh"
    echo "3. Configure your AWS CLI with admin credentials for resource creation"
    echo ""
    if [ -f ".secrets/deployment-credentials.txt" ]; then
        print_warning "Don't forget to add .secrets/deployment-credentials.txt to .gitignore!"
    fi
}

# Check for command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "AWS User and Group Setup Script"
    echo ""
    echo "This script creates:"
    echo "  • IAM Group: $GROUP_NAME"
    echo "  • IAM User: $USER_NAME"
    echo "  • Access keys for deployment"
    echo ""
    echo "Prerequisites:"
    echo "  • AWS CLI installed and configured"
    echo "  • Administrator access (AdministratorAccess policy)"
    echo "  • jq installed (optional, for automatic access key creation)"
    echo ""
    echo "Usage: $0"
    exit 0
fi

# Run main function
main "$@"
