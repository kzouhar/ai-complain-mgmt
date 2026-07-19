# WhatsApp Voice Complaint Assistant -- Deployment Guide

## Prerequisites

-   AWS Account
-   Meta WhatsApp Business App
-   OpenAI API Key
-   AWS CLI v2
-   Python 3
-   zip utility

## Project Structure

    project/
    ├── lambda/
    ├── scripts/
    │   ├── build.sh
    │   ├── deploy.sh
    │   ├── test.sh
    │   └── main.sh
    ├── template.yaml
    └── sample-webhook.json

## 1. Install AWS CLI

### macOS

``` bash
brew install awscli
```

### Windows

Download and install AWS CLI v2 from AWS.

### Linux

Follow the AWS CLI v2 installation guide.

Verify:

``` bash
aws --version
```

## 2. Configure AWS Credentials

Create an IAM user with programmatic access.

Run:

``` bash
aws configure
```

Enter:

-   AWS Access Key ID
-   AWS Secret Access Key
-   Default Region (example: us-east-1)
-   Output format: json

Verify:

``` bash
aws sts get-caller-identity
```

## 3. Required AWS Resources

Create or verify:

-   S3 bucket for Lambda packages
-   Audio media bucket
-   DynamoDB table
-   IAM deployment permissions
-   CloudFormation permissions

## 4. Meta / WhatsApp Configuration

Obtain:

-   System User Access Token
-   Phone Number ID
-   WhatsApp Business Account
-   Verify Token
-   OpenAI API Key

## 5. Set Environment Variables

``` bash
export VERIFY_TOKEN="your_verify_token"
export WHATSAPP_ACCESS_TOKEN="your_whatsapp_token"
export OPENAI_API_KEY="your_openai_key"
```

## 6. Build

``` bash
cd scripts
./build.sh
```

Packages:

-   lambda_function.zip
-   transcribe.zip

## 7. Deploy

``` bash
./deploy.sh
```

This uploads the ZIP files to S3 and deploys the CloudFormation stack.

## 8. Test

``` bash
./test.sh
```

The script retrieves the webhook URL and posts `sample-webhook.json` to
verify the deployment.

## 9. Run Everything

``` bash
./main.sh
```

The main script executes:

1.  Build
2.  Export required environment variables
3.  Deploy
4.  Test

## Troubleshooting

### AWS authentication

``` bash
aws sts get-caller-identity
```

### CloudFormation

``` bash
aws cloudformation describe-stacks --stack-name whatsapp-webhook
```

### Lambda logs

``` bash
aws logs tail /aws/lambda/whatsapp-webhook --follow
```

### Common issues

-   Missing environment variables
-   Expired WhatsApp access token
-   Missing IAM permissions
-   Incorrect S3 bucket names
-   Invalid OpenAI API key
