#!/bin/bash

echo "Starting deployment script..."
set -e

#########################################
# Configuration
#########################################

STACK_NAME="whatsapp-webhook"
BUCKET_NAME="kz-lambda-libs"
ZIP_FILE="lambda_function.zip"
TRANSCRIBE_ZIP_FILE="transcribe.zip"

VERIFY_TOKEN="khalil"
AudioMediaBucket="kz-whatsapp-audio-media"
TranscribedMediaBucketResource="kz-whatsapp-transcribed-media"
TRANSCRIPTS_TABLE="whatsapp-transcripts"
WhatsAppAccessToken="EAAZAc220jqjcBSEIUPjNNdSpB2YPcDPvbun0wayZA8TFSNR6KURIBMs3ZAx1hKagE5cyZB5qf3i27phvS185snp3WIlfG0eZALlv1kGveKKdEXDVKwl0tN2Wo8B2lOBcHhTIuBwkPdVZAZB7CZBwkNg6TonOS5AzLPbXiUkkLdlgOowCq7pHHCthDUz3e0EWZCINH9IbqPiGwjdMqaHrHQl610CS0oZCCmKBw4W8eVSeib2sntcjgZBE6chdqM5HSdfsZAcRAwvqGC3jxJ9CgUOuca7h"
OpenApiToken="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"
#########################################
# Build
#########################################

echo "Cleaning previous package..."

rm -f ${ZIP_FILE}
rm -f ${TRANSCRIBE_ZIP_FILE}

echo "Creating Lambda package..."

zip -j ${ZIP_FILE} ./lambda/lambda_function.py

rm -rf package
mkdir package

echo "Installing dependencies..."
#pip3 install --only-binary=:all: --platform manylinux2014_x86_64 -r ./lambda/requirements.txt -t package

echo "Copying source..."
cp ./lambda/transcribe.py package/

cd package

echo "Creating ZIP..."
zip -r ../transcribe.zip  .
cd ..
#zip -j ${TRANSCRIBE_ZIP_FILE} ./lambda/transcribe.py
#zip -j ${LA} ./lambda/transcribe.py

echo "Deleteing existing CloudFormation stack (if exists)..."
aws cloudformation delete-stack --stack-name ${STACK_NAME}

#########################################
# Upload
#########################################

echo "Uploading Lambda package to S3..."

#aws s3 rm s3://${BUCKET_NAME}/${ZIP_FILE} 2>/dev/null  || true
aws s3 rm s3://${BUCKET_NAME}/${TRANSCRIBE_ZIP_FILE} || true
aws s3 cp ${ZIP_FILE} s3://${BUCKET_NAME}/${ZIP_FILE}
aws s3 cp ${TRANSCRIBE_ZIP_FILE} s3://${BUCKET_NAME}/${TRANSCRIBE_ZIP_FILE}

#########################################
# Deploy
#########################################

echo "Deploying CloudFormation..."

aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name ${STACK_NAME} \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        LambdaCodeBucket=${BUCKET_NAME} \
        LambdaCodeKey=${ZIP_FILE} \
        VerifyToken=${VERIFY_TOKEN}\
        WhatsAppAccessToken=${WhatsAppAccessToken}\
        AudioMediaBucket=${AudioMediaBucket} \
        TranscriptsTable=${TRANSCRIPTS_TABLE} \
        TranscribedMediaBucket=${TranscribedMediaBucketResource}\
        OpenApiToken=${OpenApiToken}
echo ""
echo "Deployment completed."

#########################################
# Optional webhook test
#########################################

read -p "Send test webhook? (y/N): " answer

WEBHOOK_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs[?OutputKey=='CallbackURL'].OutputValue" \
    --output text)

echo ${WEBHOOK_URL}
if [[ "$answer" =~ ^[Yy]$ ]]; then


LAMBDA_FUNCTION_NAME="whatsapp-transcribe"
LAMBDA_ARN="arn:aws:lambda:us-east-1:176872086958:function:whatsapp-transcribe"
S3_BUCKET_NAME="kz-whatsapp-audio-media"

echo "Updating Lambda permission..."

aws lambda remove-permission \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --statement-id AllowS3Invoke || true

aws lambda add-permission \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --statement-id AllowS3Invoke \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::${S3_BUCKET_NAME}

echo "Updating bucket notification..."

aws s3api put-bucket-notification-configuration \
  --bucket ${S3_BUCKET_NAME} \
  --notification-configuration '{}'

aws s3api put-bucket-notification-configuration \
    --bucket ${S3_BUCKET_NAME} \
    --notification-configuration '{
      "LambdaFunctionConfigurations": [
        {
          "LambdaFunctionArn": "'${LAMBDA_ARN}'",
          "Events": ["s3:ObjectCreated:*"]
        }
      ]
    }'

aws s3api get-bucket-notification-configuration \
    --bucket ${AudioMediaBucket}   

echo "Deployment completed."


curl -X POST \
"${WEBHOOK_URL}" \
-H "Content-Type: application/json" \
-d '{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "123456789",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "phone_number_id": "1202130986315125"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Khalil"
                },
                "wa_id": "14166771640"
              }
            ],
            "messages": [
              {
                "from": "14166771640",
                "id": "wamid.TESTVOICE001",
                "timestamp": "1783500000",
                "type": "audio",
                "audio": {
                  "id": "1674133713845617",
                  "mime_type": "audio/mp4",
                  "voice": true
                }
              }
            ]
          }
        }
      ]
    }
  ]
}'

echo
echo "Webhook test completed."

fi