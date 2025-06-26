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

# Global variables
SELECTED_S3_BUCKET=""

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

# Function to search for existing S3 buckets
search_existing_s3_buckets() {
    local app_name="$1"
    local region="$2"
    
    # Reset global variable
    SELECTED_S3_BUCKET=""
    
    print_status "Searching for existing S3 buckets related to $app_name..."
    
    # List all buckets and filter for ones matching the app name pattern
    local all_buckets=$(aws s3api list-buckets --query 'Buckets[].Name' --output text 2>/dev/null || echo "")
    
    if [ -z "$all_buckets" ]; then
        print_warning "No S3 buckets found or unable to list buckets"
        return 1
    fi
    
    # Look for buckets that match our naming pattern
    local matching_buckets=""
    local app_pattern="${app_name}-deployments"
    
    for bucket in $all_buckets; do
        if [[ "$bucket" == *"$app_pattern"* ]]; then
            matching_buckets="$matching_buckets $bucket"
        fi
    done
    
    if [ -n "$matching_buckets" ]; then
        print_success "Found existing buckets matching pattern '$app_pattern':"
        echo ""
        printf "%-50s %-15s %-20s %-15s\n" "BUCKET NAME" "REGION" "CREATION DATE" "VERSIONING"
        printf "%-50s %-15s %-20s %-15s\n" "$(printf '%*s' 50 | tr ' ' '-')" "$(printf '%*s' 15 | tr ' ' '-')" "$(printf '%*s' 20 | tr ' ' '-')" "$(printf '%*s' 15 | tr ' ' '-')"
        
        for bucket in $matching_buckets; do
            # Get bucket region
            local bucket_region=$(aws s3api get-bucket-location --bucket "$bucket" --query 'LocationConstraint' --output text 2>/dev/null || echo "us-east-1")
            if [ "$bucket_region" = "None" ] || [ -z "$bucket_region" ]; then
                bucket_region="us-east-1"
            fi
            
            # Get bucket creation date
            local creation_date=$(aws s3api list-buckets --query "Buckets[?Name=='$bucket'].CreationDate" --output text 2>/dev/null || echo "Unknown")
            if [ -n "$creation_date" ] && [ "$creation_date" != "Unknown" ]; then
                creation_date=$(date -d "$creation_date" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "$creation_date")
            fi
            
            # Get versioning status
            local versioning=$(aws s3api get-bucket-versioning --bucket "$bucket" --query 'Status' --output text 2>/dev/null || echo "Disabled")
            if [ "$versioning" = "None" ] || [ -z "$versioning" ]; then
                versioning="Disabled"
            fi
            
            printf "%-50s %-15s %-20s %-15s\n" "$bucket" "$bucket_region" "$creation_date" "$versioning"
        done
        
        echo ""
        print_status "You can reuse an existing bucket or create a new one."
        
        # Convert matching_buckets to array for easier handling
        local bucket_array=($matching_buckets)
        
        # Display numbered list of available buckets
        echo ""
        echo "Available buckets for reuse:"
        local count=1
        for bucket in "${bucket_array[@]}"; do
            echo "  $count) $bucket"
            ((count++))
        done
        echo ""
        
        # Ask if user wants to use an existing bucket
        read -p "Use an existing bucket? (y/N): " use_existing
        if [[ $use_existing =~ ^[Yy]$ ]]; then
            while true; do
                read -p "Select bucket number (1-${#bucket_array[@]}): " selection
                if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#bucket_array[@]}" ]; then
                    local selected_bucket="${bucket_array[$((selection-1))]}"
                    print_success "Selected existing bucket: $selected_bucket"
                    SELECTED_S3_BUCKET="$selected_bucket"
                    return 0
                else
                    print_error "Invalid selection. Please enter a number between 1 and ${#bucket_array[@]}"
                fi
            done
        fi
    else
        print_status "No existing buckets found matching pattern '$app_pattern'"
        print_status "Will create a new bucket during setup"
    fi
    
    return 1
}

# Function to list all S3 buckets with details
list_all_s3_buckets() {
    print_status "Listing all S3 buckets in your account..."
    
    local all_buckets=$(aws s3api list-buckets --query 'Buckets[].Name' --output text 2>/dev/null || echo "")
    
    if [ -z "$all_buckets" ]; then
        print_warning "No S3 buckets found or unable to list buckets"
        return 1
    fi
    
    echo ""
    printf "%-50s %-15s %-20s %-15s %-10s\n" "BUCKET NAME" "REGION" "CREATION DATE" "VERSIONING" "SIZE"
    printf "%-50s %-15s %-20s %-15s %-10s\n" "$(printf '%*s' 50 | tr ' ' '-')" "$(printf '%*s' 15 | tr ' ' '-')" "$(printf '%*s' 20 | tr ' ' '-')" "$(printf '%*s' 15 | tr ' ' '-')" "$(printf '%*s' 10 | tr ' ' '-')"
    
    for bucket in $all_buckets; do
        # Get bucket region
        local bucket_region=$(aws s3api get-bucket-location --bucket "$bucket" --query 'LocationConstraint' --output text 2>/dev/null || echo "us-east-1")
        if [ "$bucket_region" = "None" ] || [ -z "$bucket_region" ]; then
            bucket_region="us-east-1"
        fi
        
        # Get bucket creation date
        local creation_date=$(aws s3api list-buckets --query "Buckets[?Name=='$bucket'].CreationDate" --output text 2>/dev/null || echo "Unknown")
        if [ -n "$creation_date" ] && [ "$creation_date" != "Unknown" ]; then
            creation_date=$(date -d "$creation_date" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "$creation_date")
        fi
        
        # Get versioning status
        local versioning=$(aws s3api get-bucket-versioning --bucket "$bucket" --query 'Status' --output text 2>/dev/null || echo "Disabled")
        if [ "$versioning" = "None" ] || [ -z "$versioning" ]; then
            versioning="Disabled"
        fi
        
        # Get bucket size (this can be slow for large buckets, so we'll use a simpler approach)
        local size=$(aws s3 ls s3://"$bucket" --recursive --summarize 2>/dev/null | grep "Total Size" | awk '{print $3}' || echo "Unknown")
        if [ -n "$size" ] && [ "$size" != "Unknown" ] && [ "$size" -gt 0 ] 2>/dev/null; then
            if [ "$size" -gt 1073741824 ]; then
                size="$(($size / 1073741824))GB"
            elif [ "$size" -gt 1048576 ]; then
                size="$(($size / 1048576))MB"
            elif [ "$size" -gt 1024 ]; then
                size="$(($size / 1024))KB"
            else
                size="${size}B"
            fi
        else
            size="Empty"
        fi
        
        printf "%-50s %-15s %-20s %-15s %-10s\n" "$bucket" "$bucket_region" "$creation_date" "$versioning" "$size"
    done
    
    echo ""
    local bucket_count=$(echo $all_buckets | wc -w)
    print_success "Total buckets: $bucket_count"
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

# Function to cleanup old environments
cleanup_old_environments() {
    local app_name="$1"
    
    print_status "Checking for terminated environments in application: $app_name"
    
    # Get all environments for the application
    local terminated_envs=$(aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --query 'Environments[?Status==`Terminated`].EnvironmentName' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$terminated_envs" ] && [ "$terminated_envs" != "None" ]; then
        print_warning "Found terminated environments: $terminated_envs"
        print_status "Note: Terminated environments are automatically cleaned up by AWS and cannot be manually deleted"
        print_status "They will disappear from the list after AWS completes the cleanup process"
        read -p "Continue anyway? These terminated environments will not interfere with new deployments (y/N): " continue_anyway
        if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
            print_error "Setup cancelled. You can wait for AWS to clean up terminated environments or continue anyway."
            exit 1
        fi
    else
        print_success "No terminated environments found"
    fi
}

# Function to check environment access and status
check_environment_access() {
    local app_name="$1"
    local env_name="$2"
    
    print_status "Checking access to environment: $env_name"
    
    # Check if we can access the environment
    local env_status=$(aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --environment-names "$env_name" \
        --query 'Environments[0].Status' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$env_status" = "NOT_FOUND" ] || [ "$env_status" = "None" ]; then
        print_error "Cannot access environment $env_name in application $app_name"
        print_status "This could mean:"
        print_status "1. Environment doesn't exist"
        print_status "2. Access permissions are insufficient"
        print_status "3. Environment name or application name is incorrect"
        return 1
    fi
    
    # Display environment status table
    aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --environment-names "$env_name" \
        --query 'Environments[0].{Name:EnvironmentName,Status:Status,Health:Health,Platform:PlatformArn}' \
        --output table
    
    case "$env_status" in
        "Terminated")
            print_error "Environment $env_name is terminated"
            return 1
            ;;
        "Launching"|"Updating")
            print_warning "Environment $env_name is currently $env_status"
            print_status "Wait for it to become Ready before deploying"
            return 2
            ;;
        "Ready")
            print_success "Environment $env_name is ready for deployment"
            return 0
            ;;
        *)
            print_warning "Environment $env_name is in status: $env_status"
            return 2
            ;;
    esac
}

# Function to create Elastic Beanstalk environment
create_eb_environment() {
    local app_name="$1"
    local env_name="$2"
    local instance_type="$3"
    local platform="$4"
    
    print_status "Creating Elastic Beanstalk environment: $env_name"
    
    # Check if environment already exists and get its status
    local existing_status=$(aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --environment-names "$env_name" \
        --query 'Environments[0].Status' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$existing_status" != "NOT_FOUND" ] && [ "$existing_status" != "None" ]; then
        if [ "$existing_status" = "Terminated" ]; then
            print_warning "Environment $env_name exists but is terminated"
            print_status "Terminated environments cannot be reused and will be automatically cleaned up by AWS"
            print_status "Creating new environment with the same name..."
            # No need to terminate - AWS will handle cleanup automatically
        else
            print_warning "Elastic Beanstalk environment $env_name already exists with status: $existing_status"
            return 0
        fi
    fi
    
    # Get the latest platform version with IAM instance profile
    local platform_arn=$(aws elasticbeanstalk list-platform-versions \
        --filters Type=PlatformName,Operator=contains,Values="Python 3.12" \
        --query 'PlatformSummaryList[0].PlatformArn' --output text)
    
    print_status "Creating environment with IAM instance profile..."
    
    if [ "$platform_arn" = "None" ] || [ -z "$platform_arn" ]; then
        print_warning "Could not find specific Python 3.12 platform, using solution stack name"
        aws elasticbeanstalk create-environment \
            --application-name "$app_name" \
            --environment-name "$env_name" \
            --solution-stack-name "$platform" \
            --option-settings \
                Namespace=aws:autoscaling:launchconfiguration,OptionName=InstanceType,Value="$instance_type" \
                Namespace=aws:autoscaling:launchconfiguration,OptionName=IamInstanceProfile,Value=aws-elasticbeanstalk-ec2-role \
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
                Namespace=aws:autoscaling:launchconfiguration,OptionName=IamInstanceProfile,Value=aws-elasticbeanstalk-ec2-role \
                Namespace=aws:autoscaling:asg,OptionName=MinSize,Value=1 \
                Namespace=aws:autoscaling:asg,OptionName=MaxSize,Value=1 \
                Namespace=aws:elasticbeanstalk:environment,OptionName=EnvironmentType,Value=SingleInstance \
                Namespace=aws:elasticbeanstalk:application:environment,OptionName=FLASK_ENV,Value=production \
                Namespace=aws:elasticbeanstalk:application:environment,OptionName=PYTHONPATH,Value=/var/app/current/app \
                Namespace=aws:elasticbeanstalk:container:python,OptionName=WSGIPath,Value=application.py
    fi
    
    print_success "Elastic Beanstalk environment creation initiated: $env_name"
    print_status "Environment creation may take several minutes..."
    print_status "The environment includes the required IAM instance profile: aws-elasticbeanstalk-ec2-role"
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
    print_status "Setting up AWS resources:"
    echo "  Region: $DEFAULT_REGION"
    echo "  Application: $DEFAULT_APP_NAME"
    echo "  Environment: $DEFAULT_ENV_NAME"
    echo "  Instance Type: $DEFAULT_INSTANCE_TYPE (Free Tier eligible)"
    echo "  Environment Type: Single Instance (Free Tier optimized)"
    echo ""

    # Get user input
    get_input "AWS Region" "$DEFAULT_REGION" "REGION"
    get_input "Application Name" "$DEFAULT_APP_NAME" "APP_NAME"
    get_input "Environment Name" "$DEFAULT_ENV_NAME" "ENV_NAME"
    get_input "Instance Type (use t2.micro for free tier)" "$DEFAULT_INSTANCE_TYPE" "INSTANCE_TYPE"
    
    # Search for existing S3 buckets
    echo ""
    search_existing_s3_buckets "$APP_NAME" "$REGION"
    search_result=$?
    
    if [ $search_result -eq 0 ] && [ -n "$SELECTED_S3_BUCKET" ]; then
        BUCKET_NAME="$SELECTED_S3_BUCKET"
        print_success "Using existing S3 bucket: $BUCKET_NAME"
    else
        # Generate unique S3 bucket name
        BUCKET_SUFFIX=$(generate_bucket_suffix)
        BUCKET_NAME="${APP_NAME}-deployments-${REGION}-${BUCKET_SUFFIX}"
        print_status "Will create new S3 bucket: $BUCKET_NAME"
    fi
    
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
    
    # Cleanup old terminated environments before creating new one
    cleanup_old_environments "$APP_NAME"
    
    create_eb_environment "$APP_NAME" "$ENV_NAME" "$INSTANCE_TYPE" "$DEFAULT_PLATFORM"
    
    # Check environment status after creation
    echo ""
    print_status "Checking environment status..."
    if check_environment_access "$APP_NAME" "$ENV_NAME"; then
        print_success "Environment is ready!"
    else
        print_warning "Environment may still be launching. Check status manually."
    fi
    
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --list-all-buckets     List all S3 buckets in your account"
    echo "  --help, -h             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     Run the full AWS setup process (automatically searches for existing buckets)"
    echo "  $0 --list-all-buckets  List all S3 buckets in your account"
}

# Parse command line arguments
case "${1:-}" in
    --list-all-buckets)
        check_aws_cli
        check_aws_auth
        echo "=========================================="
        echo "All S3 Buckets in Your Account"
        echo "=========================================="
        list_all_s3_buckets
        exit 0
        ;;
    --help|-h)
        show_usage
        exit 0
        ;;
    "")
        # No arguments, run main setup
        main "$@"
        ;;
    *)
        echo "Error: Unknown option '$1'"
        echo ""
        show_usage
        exit 1
        ;;
esac
