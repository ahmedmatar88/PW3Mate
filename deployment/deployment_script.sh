#!/bin/bash

# Tesla Powerwall Automation - Automated Deployment Script
# This script deploys the complete Tesla Powerwall automation system to AWS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="eu-west-1"  # Change to your preferred AWS region
ROLE_NAME="tesla-powerwall-lambda-role"
TOKEN_REFRESH_FUNCTION="tesla-daily-token-refresh"
POWERWALL_FUNCTION="tesla-powerwall-scheduler"

echo -e "${BLUE}🚀 Tesla Powerwall Automation Deployment${NC}"
echo "=========================================="

# Check prerequisites
echo -e "\n${YELLOW}📋 Checking Prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Check if AWS is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Check required files
required_files=(
    "src/lambda/token_refresh/lambda_function.py"
    "src/lambda/powerwall_scheduler/lambda_function.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}❌ Required file not found: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Get user inputs
echo -e "\n${YELLOW}🔧 Configuration${NC}"
read -p "Enter your Tesla Client ID: " CLIENT_ID
read -s -p "Enter your Tesla Client Secret: " CLIENT_SECRET
echo
read -p "Enter your Discord webhook URL: " DISCORD_WEBHOOK

if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" || -z "$DISCORD_WEBHOOK" ]]; then
    echo -e "${RED}❌ All configuration values are required${NC}"
    exit 1
fi

# Create IAM Role
echo -e "\n${YELLOW}🔐 Creating IAM Role...${NC}"

# Trust policy for Lambda
cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Permission policy for Parameter Store
cat > /tmp/permissions-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream", 
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/tesla/powerwall/*"
    }
  ]
}
EOF

# Create role if it doesn't exist
if ! aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --region "$REGION" > /dev/null
    
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "TeslaPowerwallLambdaPolicy" \
        --policy-document file:///tmp/permissions-policy.json \
        --region "$REGION" > /dev/null
    
    echo -e "${GREEN}✅ IAM role created: $ROLE_NAME${NC}"
    
    # Wait for role to be available
    echo -e "${YELLOW}⏳ Waiting for IAM role to propagate...${NC}"
    sleep 10
else
    echo -e "${BLUE}ℹ️  IAM role already exists: $ROLE_NAME${NC}"
fi

# Get account ID and construct role ARN
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

# Create Parameter Store entries
echo -e "\n${YELLOW}🗃️  Creating Parameter Store entries...${NC}"

parameters=(
    "/tesla/powerwall/client_id:$CLIENT_ID"
    "/tesla/powerwall/client_secret:$CLIENT_SECRET"
    "/tesla/powerwall/discord_webhook:$DISCORD_WEBHOOK"
    "/tesla/powerwall/access_token:placeholder-update-after-oauth"
    "/tesla/powerwall/refresh_token:placeholder-update-after-oauth"
)

for param in "${parameters[@]}"; do
    IFS=':' read -r name value <<< "$param"
    
    aws ssm put-parameter \
        --name "$name" \
        --value "$value" \
        --type "SecureString" \
        --overwrite \
        --region "$REGION" > /dev/null
    
    echo -e "${GREEN}✅ Created parameter: $name${NC}"
done

# Create deployment packages
echo -e "\n${YELLOW}📦 Creating deployment packages...${NC}"

# Create token refresh package
mkdir -p /tmp/token-refresh
cp src/lambda/token_refresh/lambda_function.py /tmp/token-refresh/
cd /tmp/token-refresh
pip install requests -t . > /dev/null 2>&1
zip -r ../token-refresh.zip . > /dev/null
cd - > /dev/null

# Create powerwall scheduler package  
mkdir -p /tmp/powerwall-scheduler
cp src/lambda/powerwall_scheduler/lambda_function.py /tmp/powerwall-scheduler/
cd /tmp/powerwall-scheduler
pip install requests -t . > /dev/null 2>&1
zip -r ../powerwall-scheduler.zip . > /dev/null
cd - > /dev/null

echo -e "${GREEN}✅ Deployment packages created${NC}"

# Deploy Lambda functions
echo -e "\n${YELLOW}⚡ Deploying Lambda functions...${NC}"

# Deploy token refresh function
if aws lambda get-function --function-name "$TOKEN_REFRESH_FUNCTION" --region "$REGION" &> /dev/null; then
    aws lambda update-function-code \
        --function-name "$TOKEN_REFRESH_FUNCTION" \
        --zip-file fileb:///tmp/token-refresh.zip \
        --region "$REGION" > /dev/null
    echo -e "${BLUE}ℹ️  Updated existing function: $TOKEN_REFRESH_FUNCTION${NC}"
else
    aws lambda create-function \
        --function-name "$TOKEN_REFRESH_FUNCTION" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file fileb:///tmp/token-refresh.zip \
        --timeout 60 \
        --memory-size 256 \
        --description "Tesla daily token refresh" \
        --region "$REGION" > /dev/null
    echo -e "${GREEN}✅ Created function: $TOKEN_REFRESH_FUNCTION${NC}"
fi

# Deploy powerwall scheduler function
if aws lambda get-function --function-name "$POWERWALL_FUNCTION" --region "$REGION" &> /dev/null; then
    aws lambda update-function-code \
        --function-name "$POWERWALL_FUNCTION" \
        --zip-file fileb:///tmp/powerwall-scheduler.zip \
        --region "$REGION" > /dev/null
    echo -e "${BLUE}ℹ️  Updated existing function: $POWERWALL_FUNCTION${NC}"
else
    aws lambda create-function \
        --function-name "$POWERWALL_FUNCTION" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file fileb:///tmp/powerwall-scheduler.zip \
        --timeout 60 \
        --memory-size 256 \
        --description "Tesla Powerwall backup reserve scheduler" \
        --region "$REGION" > /dev/null
    echo -e "${GREEN}✅ Created function: $POWERWALL_FUNCTION${NC}"
fi

# Create EventBridge rules
echo -e "\n${YELLOW}⏰ Creating EventBridge schedules...${NC}"

LAMBDA_ARN_TOKEN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${TOKEN_REFRESH_FUNCTION}"
LAMBDA_ARN_POWERWALL="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${POWERWALL_FUNCTION}"

# Token refresh schedules
schedules=(
    "tesla-token-refresh-9pm:cron(0 20 * * ? *):$LAMBDA_ARN_TOKEN:{}"
    "tesla-token-refresh-10pm:cron(0 21 * * ? *):$LAMBDA_ARN_TOKEN:{}"
    "tesla-powerwall-2331-100percent:cron(31 22 * * ? *):$LAMBDA_ARN_POWERWALL:{\"backup_reserve_percent\":100,\"schedule_name\":\"11:31 PM - Set to 100%\"}"
    "tesla-powerwall-2329-0percent:cron(29 23 * * ? *):$LAMBDA_ARN_POWERWALL:{\"backup_reserve_percent\":0,\"schedule_name\":\"12:29 AM - Set to 0%\"}"
    "tesla-powerwall-0131-100percent:cron(31 0 * * ? *):$LAMBDA_ARN_POWERWALL:{\"backup_reserve_percent\":100,\"schedule_name\":\"1:31 AM - Set to 100%\"}"
    "tesla-powerwall-0529-0percent:cron(29 4 * * ? *):$LAMBDA_ARN_POWERWALL:{\"backup_reserve_percent\":0,\"schedule_name\":\"5:29 AM - Set to 0%\"}"
)

for schedule in "${schedules[@]}"; do
    IFS=':' read -r rule_name cron_expr lambda_arn input_json <<< "$schedule"
    
    # Create EventBridge rule
    aws events put-rule \
        --name "$rule_name" \
        --schedule-expression "$cron_expr" \
        --description "Tesla Powerwall automation schedule" \
        --region "$REGION" > /dev/null
    
    # Add Lambda permission
    aws lambda add-permission \
        --function-name "${lambda_arn##*:}" \
        --statement-id "EventBridge-${rule_name}" \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn "arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/${rule_name}" \
        --region "$REGION" > /dev/null 2>&1 || true
    
    # Add target to rule
    aws events put-targets \
        --rule "$rule_name" \
        --targets "Id=1,Arn=${lambda_arn},Input='${input_json}'" \
        --region "$REGION" > /dev/null
    
    echo -e "${GREEN}✅ Created schedule: $rule_name${NC}"
done

# Cleanup temporary files
rm -rf /tmp/token-refresh /tmp/powerwall-scheduler
rm -f /tmp/token-refresh.zip /tmp/powerwall-scheduler.zip
rm -f /tmp/trust-policy.json /tmp/permissions-policy.json

# Final instructions
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo "========================"
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Complete Tesla Fleet API OAuth flow to get initial tokens"
echo "2. Update Parameter Store with real access_token and refresh_token"
echo "3. Test the Lambda functions manually"
echo "4. Monitor Discord for notifications"
echo
echo -e "${YELLOW}🧪 Test Commands:${NC}"
echo "# Test token refresh:"
echo "aws lambda invoke --function-name $TOKEN_REFRESH_FUNCTION response.json --region $REGION"
echo
echo "# Test powerwall scheduler:"
echo "aws lambda invoke --function-name $POWERWALL_FUNCTION --payload '{\"backup_reserve_percent\":50,\"schedule_name\":\"Test\"}' response.json --region $REGION"
echo
echo -e "${YELLOW}📊 Monitor Logs:${NC}"
echo "aws logs tail /aws/lambda/$TOKEN_REFRESH_FUNCTION --follow --region $REGION"
echo "aws logs tail /aws/lambda/$POWERWALL_FUNCTION --follow --region $REGION"
echo
echo -e "${YELLOW}💰 Estimated Monthly Cost: ~$0.01${NC}"
echo
echo -e "${GREEN}✨ Your Tesla Powerwall automation system is ready!${NC}"
