#!/bin/bash

# AWS Resources Check and Cleanup Script for Airspace Viewer
# This script checks the status of AWS resources and can clean up terminated environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_REGION="eu-west-1"
DEFAULT_APP_NAME="airspace-viewer"
DEFAULT_ENV_NAME="airspace-viewer-prod"

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
        exit 1
    fi
}

# Function to check if user is authenticated
check_aws_auth() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured or credentials are invalid."
        echo "Please run 'aws configure' first to set up your credentials."
        exit 1
    fi
    
    local current_user=$(aws sts get-caller-identity --query 'Arn' --output text)
    print_success "Authenticated as: $current_user"
}

# Function to check environment access and status
check_environment_access() {
    local app_name="$1"
    local env_name="$2"
    
    print_status "Checking access to environment: $env_name"
    
    # Check if we can access the environment
    local env_info=$(aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --environment-names "$env_name" \
        --query 'Environments[0]' \
        --output json 2>/dev/null || echo "null")
    
    if [ "$env_info" = "null" ] || [ "$(echo "$env_info" | jq -r '.EnvironmentName // "null"')" = "null" ]; then
        print_error "Cannot access environment $env_name in application $app_name"
        print_status "This could mean:"
        print_status "1. Environment doesn't exist"
        print_status "2. Access permissions are insufficient"
        print_status "3. Environment name or application name is incorrect"
        return 1
    fi
    
    # Display environment status table
    echo ""
    echo "Environment Details:"
    echo "==================="
    aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --environment-names "$env_name" \
        --query 'Environments[0].{Name:EnvironmentName,Status:Status,Health:Health,URL:EndpointURL,Created:DateCreated,Updated:DateUpdated}' \
        --output table
    
    local env_status=$(echo "$env_info" | jq -r '.Status')
    
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
            local endpoint=$(echo "$env_info" | jq -r '.EndpointURL // "None"')
            if [ "$endpoint" != "None" ]; then
                print_success "Application URL: $endpoint"
            fi
            return 0
            ;;
        *)
            print_warning "Environment $env_name is in status: $env_status"
            return 2
            ;;
    esac
}

# Function to list all environments in application
list_all_environments() {
    local app_name="$1"
    
    print_status "Listing all environments in application: $app_name"
    
    local envs=$(aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --query 'Environments' \
        --output json 2>/dev/null || echo "[]")
    
    if [ "$envs" = "[]" ] || [ "$(echo "$envs" | jq 'length')" = "0" ]; then
        print_warning "No environments found in application $app_name"
        return 1
    fi
    
    echo ""
    echo "All Environments:"
    echo "================="
    aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --query 'Environments[].{Name:EnvironmentName,Status:Status,Health:Health,Created:DateCreated}' \
        --output table
    
    # Count environments by status
    local ready_count=$(echo "$envs" | jq '[.[] | select(.Status == "Ready")] | length')
    local terminated_count=$(echo "$envs" | jq '[.[] | select(.Status == "Terminated")] | length')
    local other_count=$(echo "$envs" | jq '[.[] | select(.Status != "Ready" and .Status != "Terminated")] | length')
    
    echo ""
    print_status "Summary:"
    echo "  Ready: $ready_count"
    echo "  Terminated: $terminated_count"
    echo "  Other: $other_count"
    
    return 0
}

# Function to cleanup terminated environments
cleanup_terminated_environments() {
    local app_name="$1"
    
    print_status "Checking for terminated environments in application: $app_name"
    
    # Get terminated environments
    local terminated_envs=$(aws elasticbeanstalk describe-environments \
        --application-name "$app_name" \
        --query 'Environments[?Status==`Terminated`].EnvironmentName' \
        --output json 2>/dev/null || echo "[]")
    
    if [ "$terminated_envs" = "[]" ] || [ "$(echo "$terminated_envs" | jq 'length')" = "0" ]; then
        print_success "No terminated environments found"
        return 0
    fi
    
    echo "Terminated environments found:"
    echo "$terminated_envs" | jq -r '.[]' | while read env; do
        echo "  - $env"
    done
    
    echo ""
    print_warning "Terminated environments take up space and should be cleaned up"
    read -p "Remove all terminated environments? (y/N): " cleanup_confirmed
    
    if [[ $cleanup_confirmed =~ ^[Yy]$ ]]; then
        echo "$terminated_envs" | jq -r '.[]' | while read env; do
            print_status "Removing terminated environment: $env"
            if aws elasticbeanstalk delete-environment \
                --environment-name "$env" \
                --terminate-env-by-force 2>/dev/null; then
                print_success "Successfully queued $env for deletion"
            else
                print_warning "Could not delete $env (may already be gone)"
            fi
        done
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to check S3 bucket
check_s3_bucket() {
    local bucket_name="$1"
    
    print_status "Checking S3 bucket: $bucket_name"
    
    if ! aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        print_error "Cannot access S3 bucket: $bucket_name"
        print_status "This could mean:"
        print_status "1. Bucket doesn't exist"
        print_status "2. No permission to access bucket"
        print_status "3. Bucket name is incorrect"
        return 1
    fi
    
    # Get bucket info
    local region=$(aws s3api get-bucket-location --bucket "$bucket_name" --query 'LocationConstraint' --output text 2>/dev/null || echo "us-east-1")
    if [ "$region" = "None" ]; then
        region="us-east-1"
    fi
    
    local versioning=$(aws s3api get-bucket-versioning --bucket "$bucket_name" --query 'Status' --output text 2>/dev/null || echo "Disabled")
    
    print_success "S3 bucket is accessible"
    echo "  Region: $region"
    echo "  Versioning: $versioning"
    
    # Count objects
    local object_count=$(aws s3api list-objects-v2 --bucket "$bucket_name" --query 'KeyCount' --output text 2>/dev/null || echo "0")
    echo "  Objects: $object_count"
    
    return 0
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

# Main function
main() {
    local action="$1"
    
    echo "=========================================="
    echo "AWS Resources Check for Airspace Viewer"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_aws_cli
    check_aws_auth
    
    echo ""
    
    # Get configuration
    get_input "AWS Region" "$DEFAULT_REGION" "REGION"
    get_input "Application Name" "$DEFAULT_APP_NAME" "APP_NAME"
    get_input "Environment Name" "$DEFAULT_ENV_NAME" "ENV_NAME"
    
    # Try to determine S3 bucket name from deploy.yml
    local bucket_name=""
    if [ -f ".github/workflows/deploy.yml" ]; then
        bucket_name=$(grep "EB_S3_BUCKET:" .github/workflows/deploy.yml | cut -d: -f2 | xargs 2>/dev/null || echo "")
    fi
    
    if [ -z "$bucket_name" ]; then
        get_input "S3 Bucket Name (optional)" "" "BUCKET_NAME"
        bucket_name="$BUCKET_NAME"
    fi
    
    echo ""
    print_status "Configuration:"
    echo "  Region: $REGION"
    echo "  Application: $APP_NAME"
    echo "  Environment: $ENV_NAME"
    if [ -n "$bucket_name" ]; then
        echo "  S3 Bucket: $bucket_name"
    fi
    echo ""
    
    case "$action" in
        "check"|"")
            # Check specific environment
            check_environment_access "$APP_NAME" "$ENV_NAME"
            
            # Check S3 bucket if provided
            if [ -n "$bucket_name" ]; then
                echo ""
                check_s3_bucket "$bucket_name"
            fi
            ;;
        "list")
            # List all environments
            list_all_environments "$APP_NAME"
            ;;
        "cleanup")
            # Cleanup terminated environments
            cleanup_terminated_environments "$APP_NAME"
            ;;
        "all")
            # Do everything
            check_environment_access "$APP_NAME" "$ENV_NAME"
            echo ""
            list_all_environments "$APP_NAME"
            echo ""
            cleanup_terminated_environments "$APP_NAME"
            
            if [ -n "$bucket_name" ]; then
                echo ""
                check_s3_bucket "$bucket_name"
            fi
            ;;
        "help"|"--help"|"-h")
            echo "Usage: $0 [action]"
            echo ""
            echo "Actions:"
            echo "  check (default) - Check specific environment and S3 bucket"
            echo "  list           - List all environments in application"
            echo "  cleanup        - Remove terminated environments"
            echo "  all            - Perform all checks and cleanup"
            echo "  help           - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0              # Check main environment"
            echo "  $0 list         # List all environments"
            echo "  $0 cleanup      # Clean up terminated environments"
            echo "  $0 all          # Full check and cleanup"
            exit 0
            ;;
        *)
            print_error "Unknown action: $action"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "Resource check completed!"
}

# Check for jq dependency
if ! command -v jq &> /dev/null; then
    print_error "jq is required but not installed."
    echo "Please install jq: https://stedolan.github.io/jq/download/"
    exit 1
fi

# Run main function
main "$@"
