#!/bin/bash
# ============================================================================
# PW3Mate CloudFormation Deployment Script
# ============================================================================
# Usage:
#   ./deploy.sh <S3_BUCKET> [STACK_NAME] [AWS_REGION]
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - An S3 bucket for Lambda deployment packages
#   - Tesla OAuth tokens (from the OAuth flow)
#
# Example:
#   ./deploy.sh my-pw3mate-deploy-bucket PW3Mate eu-west-1
# ============================================================================

set -euo pipefail

# --------------------------------------------------------------------------
# Arguments
# --------------------------------------------------------------------------
S3_BUCKET="${1:?Usage: ./deploy.sh <S3_BUCKET> [STACK_NAME] [AWS_REGION]}"
STACK_NAME="${2:-PW3Mate}"
AWS_REGION="${3:-eu-west-1}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_DIR/src/lambda"

echo "============================================"
echo "  PW3Mate CloudFormation Deployment"
echo "============================================"
echo "  S3 Bucket:  $S3_BUCKET"
echo "  Stack Name: $STACK_NAME"
echo "  Region:     $AWS_REGION"
echo "============================================"

# --------------------------------------------------------------------------
# Step 1: Package Lambda functions
# --------------------------------------------------------------------------
echo ""
echo "[1/4] Packaging Lambda functions..."

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Package token_refresh
echo "  - Packaging token_refresh..."
cd "$SRC_DIR/token_refresh"
zip -q "$TEMP_DIR/token_refresh.zip" lamda_function.py
echo "    Done."

# Package powerwall_scheduler
echo "  - Packaging powerwall_scheduler..."
cd "$SRC_DIR/powerwall_scheduler"
zip -q "$TEMP_DIR/powerwall_scheduler.zip" lambda_function.py
echo "    Done."

# Package schedule_manager
echo "  - Packaging schedule_manager..."
cd "$SRC_DIR/schedule_manager"
zip -q "$TEMP_DIR/schedule_manager.zip" lambda_function.py
echo "    Done."

# Package requests layer
echo "  - Packaging requests Lambda layer..."
LAYER_DIR="$TEMP_DIR/python"
mkdir -p "$LAYER_DIR"
pip install requests -t "$LAYER_DIR" --quiet --no-cache-dir
cd "$TEMP_DIR"
zip -qr "$TEMP_DIR/requests-layer.zip" python/
echo "    Done."

cd "$SCRIPT_DIR"

# --------------------------------------------------------------------------
# Step 2: Upload to S3
# --------------------------------------------------------------------------
echo ""
echo "[2/4] Uploading packages to S3..."

aws s3 cp "$TEMP_DIR/token_refresh.zip" "s3://$S3_BUCKET/lambda/token_refresh.zip" --region "$AWS_REGION"
aws s3 cp "$TEMP_DIR/powerwall_scheduler.zip" "s3://$S3_BUCKET/lambda/powerwall_scheduler.zip" --region "$AWS_REGION"
aws s3 cp "$TEMP_DIR/schedule_manager.zip" "s3://$S3_BUCKET/lambda/schedule_manager.zip" --region "$AWS_REGION"
aws s3 cp "$TEMP_DIR/requests-layer.zip" "s3://$S3_BUCKET/lambda/requests-layer.zip" --region "$AWS_REGION"

echo "  All packages uploaded."

# --------------------------------------------------------------------------
# Step 3: Collect parameters
# --------------------------------------------------------------------------
echo ""
echo "[3/4] Collecting parameters..."

read -rp "  Tesla Client ID: " TESLA_CLIENT_ID
read -rsp "  Tesla Client Secret: " TESLA_CLIENT_SECRET; echo ""
read -rsp "  Tesla Access Token: " TESLA_ACCESS_TOKEN; echo ""
read -rsp "  Tesla Refresh Token: " TESLA_REFRESH_TOKEN; echo ""
read -rp "  Discord Webhook URL (press Enter to skip): " DISCORD_WEBHOOK
read -rsp "  UI Password (press Enter to skip): " UI_PASSWORD; echo ""

# --------------------------------------------------------------------------
# Step 4: Deploy CloudFormation stack
# --------------------------------------------------------------------------
echo ""
echo "[4/4] Deploying CloudFormation stack..."

aws cloudformation deploy \
  --template-file "$SCRIPT_DIR/pw3mate-stack.yaml" \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    TeslaClientId="$TESLA_CLIENT_ID" \
    TeslaClientSecret="$TESLA_CLIENT_SECRET" \
    TeslaAccessToken="$TESLA_ACCESS_TOKEN" \
    TeslaRefreshToken="$TESLA_REFRESH_TOKEN" \
    DiscordWebhookUrl="${DISCORD_WEBHOOK:-}" \
    UIPassword="${UI_PASSWORD:-}" \
    LambdaS3Bucket="$S3_BUCKET"

echo ""
echo "============================================"
echo "  Deployment Complete!"
echo "============================================"

# Show outputs
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs' \
  --output table

echo ""
echo "Done! Your PW3Mate stack is now live."
