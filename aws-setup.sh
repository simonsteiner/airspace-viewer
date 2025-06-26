#!/bin/bash

# AWS Elastic Beanstalk Setup Script for Airspace Viewer
# This script sets up AWS resources for first-time deployment
# Default region: eu-west-1

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values (Free Tier eligible)
DEFAULT_REGION="eu-west-1"
DEFAULT_APP_NAME="airspace-viewer"
DEFAULT_ENV_NAME="airspace-viewer-prod"
DEFAULT_INSTANCE_TYPE="t2.micro"  # Free tier eligible
DEFAULT_PLATFORM="64bit Amazon Linux 2023 v4.3.0 running Python 3.12"

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

# Function to check if user is authenticated
check_aws_auth() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured or credentials are invalid."
        echo "Please run 'aws configure' first to set up your credentials."
        exit 1
    fi
    print_success "AWS credentials are configured"
}

# Function to get user input with default
get_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    read -p "$prompt [$default]: " input
    if [ -z "$input" ]; then
        eval "$var_name='$default'"
    else
        eval "$var_name='$input'"
    fi
}

# Function to generate random string for S3 bucket
generate_bucket_suffix() {
    echo $(date +%s | tail -c 6)$(openssl rand -hex 3)
}

# Function to create S3 bucket
create_s3_bucket() {
    local bucket_name="$1"
    local region="$2"
    
    print_status "Creating S3 bucket: $bucket_name"
    
    if aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        print_warning "S3 bucket $bucket_name already exists"
        return 0
    fi
    
    if [ "$region" = "us-east-1" ]; then
        aws s3api create-bucket --bucket "$bucket_name" --region "$region"
    else
        aws s3api create-bucket --bucket "$bucket_name" --region "$region" \
            --create-bucket-configuration LocationConstraint="$region"
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning --bucket "$bucket_name" \
        --versioning-configuration Status=Enabled
    
    print_success "S3 bucket created: $bucket_name"
}

# Function to create Elastic Beanstalk application
create_eb_application() {
    local app_name="$1"
    
    print_status "Creating Elastic Beanstalk application: $app_name"
    
    if aws elasticbeanstalk describe-applications --application-names "$app_name" 2>/dev/null | grep -q "$app_name"; then
        print_warning "Elastic Beanstalk application $app_name already exists"
        return 0
    fi
    
    aws elasticbeanstalk create-application \
        --application-name "$app_name" \
        --description "Airspace Viewer - OpenAir file viewer and converter"
    
    print_success "Elastic Beanstalk application created: $app_name"
}

# Function to create Elastic Beanstalk environment
create_eb_environment() {
    local app_name="$1"
    local env_name="$2"
    local instance_type="$3"
    local platform="$4"
    
    print_status "Creating Elastic Beanstalk environment: $env_name"
    
    if aws elasticbeanstalk describe-environments --application-name "$app_name" --environment-names "$env_name" 2>/dev/null | grep -q "$env_name"; then
        print_warning "Elastic Beanstalk environment $env_name already exists"
        return 0
    fi
    
    # Get the latest platform version
    local platform_arn=$(aws elasticbeanstalk list-platform-versions \
        --filters Type=PlatformName,Operator=contains,Values="Python 3.12" \
        --query 'PlatformSummaryList[0].PlatformArn' --output text)
    
    if [ "$platform_arn" = "None" ] || [ -z "$platform_arn" ]; then
        print_warning "Could not find specific Python 3.12 platform, using solution stack name"
        aws elasticbeanstalk create-environment \
            --application-name "$app_name" \
            --environment-name "$env_name" \
            --solution-stack-name "$platform" \
            --option-settings \
                Namespace=aws:autoscaling:launchconfiguration,OptionName=InstanceType,Value="$instance_type" \
                Namespace=aws:autoscaling:asg,OptionName=MinSize,Value=1 \
                Namespace=aws:autoscaling:asg,OptionName=MaxSize,Value=1 \
                Namespace=aws:elasticbeanstalk:environment,OptionName=EnvironmentType,Value=SingleInstance \
                Namespace=aws:elasticbeanstalk:application:environment,OptionName=FLASK_ENV,Value=production \
                Namespace=aws:elasticbeanstalk:application:environment,OptionName=PYTHONPATH,Value=/var/app/current/app \
                Namespace=aws:elasticbeanstalk:container:python,OptionName=WSGIPath,Value=application.py
    else
        aws elasticbeanstalk create-environment \
            --application-name "$app_name" \
            --environment-name "$env_name" \
            --platform-arn "$platform_arn" \
            --option-settings \
                Namespace=aws:autoscaling:launchconfiguration,OptionName=InstanceType,Value="$instance_type" \
                Namespace=aws:autoscaling:asg,OptionName=MinSize,Value=1 \
                Namespace=aws:autoscaling:asg,OptionName=MaxSize,Value=1 \
                Namespace=aws:elasticbeanstalk:environment,OptionName=EnvironmentType,Value=SingleInstance \
                Namespace=aws:elasticbeanstalk:application:environment,OptionName=FLASK_ENV,Value=production \
                Namespace=aws:elasticbeanstalk:application:environment,OptionName=PYTHONPATH,Value=/var/app/current/app \
                Namespace=aws:elasticbeanstalk:container:python,OptionName=WSGIPath,Value=application.py
    fi
    
    print_success "Elastic Beanstalk environment creation initiated: $env_name"
    print_status "Environment creation may take several minutes..."
}

# Function to generate secrets
generate_secrets() {
    local app_name="$1"
    local env_name="$2"
    local bucket_name="$3"
    local region="$4"
    
    print_status "Generating GitHub Actions secrets configuration..."
    
    # Generate Flask secret key
    local flask_secret=$(openssl rand -base64 32)
    
    cat > .secrets/github-secrets.txt << EOF
# GitHub Actions Secrets Configuration
# Add these SECRETS to your GitHub repository:
# Go to Settings > Secrets and variables > Actions > New repository secret

# Required Secrets:
AWS_ACCESS_KEY_ID=<your-deployment-user-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-deployment-user-secret-access-key>
FLASK_SECRET_KEY=$flask_secret

# Configuration Values (update in .github/workflows/deploy.yml env section):
    env:
      AWS_REGION: $region
      EB_APP_NAME: $app_name
      EB_ENV_NAME: $env_name
      EB_S3_BUCKET: $bucket_name

# Required IAM policies for deployment user (via group):
# - AmazonS3FullAccess
# - AdministratorAccess-AWSElasticBeanstalk
EOF
    
    print_success "Secrets configuration saved to .secrets/github-secrets.txt"
}

# Function to validate free tier eligibility
validate_free_tier() {
    local instance_type="$1"
    local region="$2"
    
    # Check if instance type is free tier eligible
    if [[ "$instance_type" != "t2.micro" ]]; then
        print_warning "Instance type $instance_type is NOT free tier eligible!"
        print_status "Free tier eligible instance types: t2.micro"
        read -p "Continue anyway? This may incur charges. (y/N): " continue_paid
        if [[ ! $continue_paid =~ ^[Yy]$ ]]; then
            print_error "Setup cancelled. Use t2.micro for free tier."
            exit 1
        fi
    else
        print_success "Instance type $instance_type is free tier eligible"
    fi
    
    # Warn about region-specific free tier availability
    print_status "Note: Free tier is available in all AWS regions, but some services may have regional limitations"
}

# Main setup function
main() {
    echo "=========================================="
    echo "AWS Elastic Beanstalk Setup for Airspace Viewer"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_aws_cli
    check_aws_auth
    
    echo ""
    print_status "Setting up AWS resources with FREE TIER eligible defaults:"
    echo "  Region: $DEFAULT_REGION"
    echo "  Application: $DEFAULT_APP_NAME"
    echo "  Environment: $DEFAULT_ENV_NAME"
    echo "  Instance Type: $DEFAULT_INSTANCE_TYPE (Free Tier eligible)"
    echo "  Environment Type: Single Instance (Free Tier optimized)"
    echo ""
    print_warning "Free Tier limits:"
    echo "  • 750 hours/month of t2.micro instances"
    echo "  • 5GB of S3 storage"
    echo "  • Single instance deployment (no load balancer)"
    echo ""
    
    # Get user input
    get_input "AWS Region" "$DEFAULT_REGION" "REGION"
    get_input "Application Name" "$DEFAULT_APP_NAME" "APP_NAME"
    get_input "Environment Name" "$DEFAULT_ENV_NAME" "ENV_NAME"
    get_input "Instance Type (use t2.micro for free tier)" "$DEFAULT_INSTANCE_TYPE" "INSTANCE_TYPE"
    
    # Validate free tier eligibility
    validate_free_tier "$INSTANCE_TYPE" "$REGION"
    
    # Validate free tier eligibility
    validate_free_tier "$INSTANCE_TYPE" "$REGION"
    
    # Generate unique S3 bucket name
    BUCKET_SUFFIX=$(generate_bucket_suffix)
    BUCKET_NAME="${APP_NAME}-deployments-${DEFAULT_REGION}-${BUCKET_SUFFIX}"
    
    echo ""
    print_status "Configuration (Free Tier Optimized):"
    echo "  Region: $REGION"
    echo "  App Name: $APP_NAME"
    echo "  Environment: $ENV_NAME"
    echo "  Instance Type: $INSTANCE_TYPE"
    echo "  S3 Bucket: $BUCKET_NAME"
    echo "  Environment Type: Single Instance (no load balancer)"
    echo ""
    print_success "This configuration stays within AWS Free Tier limits!"
    echo ""
    
    read -p "Continue with setup? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_error "Setup cancelled"
        exit 1
    fi
    
    echo ""
    print_status "Starting AWS resource creation..."
    
    # Create resources
    create_s3_bucket "$BUCKET_NAME" "$REGION"
    create_eb_application "$APP_NAME"
    create_eb_environment "$APP_NAME" "$ENV_NAME" "$INSTANCE_TYPE" "$DEFAULT_PLATFORM"
    
    # Generate secrets configuration
    generate_secrets "$APP_NAME" "$ENV_NAME" "$BUCKET_NAME" "$REGION"
    
    echo ""
    print_success "AWS setup completed!"
    echo ""
    print_success "FREE TIER SUMMARY:"
    echo "✓ t2.micro instance (750 hours/month free)"
    echo "✓ Single instance deployment (no load balancer charges)"
    echo "✓ S3 bucket with versioning (5GB free storage)"
    echo "✓ Elastic Beanstalk (no additional charges)"
    echo ""
    echo "Next steps:"
    echo "1. Wait for the Elastic Beanstalk environment to finish creating (5-10 minutes)"
    echo "2. Check .secrets/github-secrets.txt for the secrets to add to your GitHub repository"
    echo "3. Use your IAM user credentials (from Prerequisites) for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    echo "4. Add the secrets to GitHub: Settings > Secrets and variables > Actions"
    echo "5. Push code to main branch to trigger deployment"
    echo ""
    echo "You can check the environment status with:"
    echo "  aws elasticbeanstalk describe-environments --application-name $APP_NAME --environment-names $ENV_NAME"
    echo ""
    print_warning "Monitor your AWS usage to stay within free tier limits!"
    print_warning "Keep your AWS credentials secure and never commit them to version control!"
}

# Run main function
main "$@"
