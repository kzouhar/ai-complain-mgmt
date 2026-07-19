#!/bin/bash
set -e

STACK_NAME="whatsapp-webhook"

WEBHOOK_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='CallbackURL'].OutputValue" \
  --output text)

curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d @sample-webhook.json

echo
echo "Webhook test completed."
