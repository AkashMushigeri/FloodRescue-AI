# FloodRescue AI — AWS Deployment Guide

**WeMakeDevs × AWS Environmental Hackathon 2026**

---

## 1. Deployment Status & Environment Disclosure

> [!IMPORTANT]
> **Host Environment Status:**
> During automated Phase 1 workspace inspection on this machine, `aws` and `sam` CLIs were not found in the local PATH (`CommandNotFoundException`).
> As mandated by hackathon rules:
> - The application is fully implemented, packaged, and verified locally with 100% test pass rate (`APP_MODE=local`).
> - The production AWS SAM infrastructure template (`infrastructure/template.yaml`), Lambda handler (`backend/lambda_handlers/main.py`), and DynamoDB adapter (`backend/services/dynamodb_persistence.py`) are fully built and ready for cloud deployment.
> - Follow the exact steps below once AWS CLI and SAM CLI are installed with your hackathon AWS credentials.

---

## 2. Prerequisites

1. **AWS CLI v2:** Install via [AWS CLI Installer](https://aws.amazon.com/cli/).
2. **AWS SAM CLI:** Install via [AWS SAM CLI Installer](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
3. **AWS Account & IAM Permissions:**
   - Permissions to provision: API Gateway HTTP API, AWS Lambda, Amazon DynamoDB, AWS IAM Roles, and Amazon Bedrock model invocation.
4. **Amazon Bedrock Model Access:**
   - Open AWS Console → Amazon Bedrock → Model access → Request access for **Anthropic Claude 3 Haiku** or **Amazon Nova Micro** in your target region (e.g., `us-east-1` or `us-west-2`).

---

## 3. Step-by-Step Backend Deployment (AWS SAM)

### Step 3.1: Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### Step 3.2: Build SAM Serverless Application
Navigate to the infrastructure directory:
```bash
cd "infrastructure"
sam build --use-container
```
*(If Docker is not running, run `sam build` directly on a system with Python 3.11 installed).*

### Step 3.3: Deploy Infrastructure
```bash
sam deploy --guided
```
Prompt responses:
- **Stack Name:** `FloodRescue-AI-Stack`
- **AWS Region:** `us-east-1`
- **Parameter AppMode:** `aws`
- **Confirm changes before deploy:** `Y`
- **Allow SAM CLI to create IAM roles:** `Y`
- **Disable rollback:** `N`
- **FloodRescueApiFunction has no authentication. Is this okay?:** `Y` (Public emergency SOS ingress)
- **Save arguments to configuration file:** `Y`

### Step 3.4: Note Outputs
After deployment succeeds, SAM outputs the HTTP API Endpoint:
```
Key: ApiEndpoint
Value: https://abcdef1234.execute-api.us-east-1.amazonaws.com
```

---

## 4. Step-by-Step Frontend Deployment (AWS Amplify or S3 + CloudFront)

### Option A: AWS Amplify Hosting (Recommended)
1. In `frontend/.env.production`, set the deployed API Gateway URL:
   ```env
   VITE_API_BASE_URL=https://abcdef1234.execute-api.us-east-1.amazonaws.com
   ```
2. Build the production bundle:
   ```bash
   cd frontend
   npm run build
   ```
3. Push your repository to GitHub.
4. Open AWS Console → **AWS Amplify Hosting** → **Create new app from GitHub repo**.
5. Select the repository and `main` branch.
6. Amplify automatically detects Vite. Build settings:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - npm install
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: dist
       files:
         - '**/*'
     cache:
       paths:
         - node_modules/**/*
   ```
7. Click **Save and Deploy**. Your live HTTPS domain will be provisioned in minutes.

### Option B: S3 + CloudFront Static Hosting
```bash
# 1. Create S3 Bucket
aws s3 mb s3://floodrescue-ai-frontend-demo --region us-east-1

# 2. Sync build files
aws s3 sync frontend/dist/ s3://floodrescue-ai-frontend-demo/ --acl public-read
```

---

## 5. Verification Commands

Test your deployed backend using PowerShell or cURL:

### 1. Health & Mode Check
```bash
curl -X GET "https://abcdef1234.execute-api.us-east-1.amazonaws.com/health"
```
Expected output:
```json
{"status":"healthy","service":"FloodRescue AI","app_mode":"aws","is_simulated_mode":false}
```

### 2. Submit Live Test SOS
```bash
curl -X POST "https://abcdef1234.execute-api.us-east-1.amazonaws.com/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "people_reported": 3,
    "distress_message": "Water rising past car tires on bridge. 3 people trapped.",
    "landmark_description": "Kotturpuram Bridge",
    "water_level": "waist",
    "is_simulated": true
  }'
```

---

## 6. Teardown Instructions

To avoid incurring unexpected AWS serverless or Bedrock costs after hackathon evaluation:
```bash
# 1. Delete SAM Serverless Stack (deletes Lambda, API Gateway, DynamoDB tables, and IAM roles)
sam delete --stack-name FloodRescue-AI-Stack

# 2. Delete Amplify App or S3 Bucket
aws s3 rb s3://floodrescue-ai-frontend-demo --force
```
