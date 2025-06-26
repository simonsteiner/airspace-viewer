#!/bin/bash

# Quick commands to check existing AWS resources

echo "=== S3 Buckets containing 'airspace-viewer' ==="
aws s3api list-buckets --query "Buckets[?contains(Name, 'airspace-viewer')].{Name:Name,CreationDate:CreationDate}" --output table

echo ""
echo "=== Elastic Beanstalk Applications ==="
aws elasticbeanstalk describe-applications --query "Applications[?contains(ApplicationName, 'airspace-viewer')].{Name:ApplicationName,Description:Description}" --output table

echo ""
echo "=== Elastic Beanstalk Environments ==="
aws elasticbeanstalk describe-environments --query "Environments[?contains(ApplicationName, 'airspace-viewer')].{App:ApplicationName,Environment:EnvironmentName,Status:Status,Health:Health,URL:CNAME}" --output table

echo ""
echo "=== Current AWS Region ==="
aws configure get region

echo ""
echo "=== Current AWS Account ==="
aws sts get-caller-identity --query "Account" --output text
