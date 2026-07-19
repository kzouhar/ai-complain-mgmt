#!/bin/bash
set -e

STACK_NAME="whatsapp-webhook"
CODE_BUCKET="kz-lambda-libs"

: "${VERIFY_TOKEN:?Missing VERIFY_TOKEN}"
: "${WHATSAPP_ACCESS_TOKEN:?Missing WHATSAPP_ACCESS_TOKEN}"
: "${OPENAI_API_KEY:?Missing OPENAI_API_KEY}"

aws s3 cp lambda_function.zip s3://$CODE_BUCKET/lambda_function.zip
aws s3 cp transcribe.zip s3://$CODE_BUCKET/transcribe.zip

aws cloudformation deploy \
  --template-file ../template.yaml \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
  LambdaCodeBucket=$CODE_BUCKET \
  LambdaCodeKey=lambda_function.zip \
  VerifyToken=$VERIFY_TOKEN \
  WhatsAppAccessToken=$WHATSAPP_ACCESS_TOKEN \
  OpenApiToken=$OPENAI_API_KEY

echo "Deployment complete."
