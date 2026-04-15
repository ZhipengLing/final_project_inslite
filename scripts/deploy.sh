#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "========================================="
echo "  InstaLite — Full Deploy"
echo "========================================="

echo ""
echo "[1/5] Building Lambda Layer..."
cd layers/common
chmod +x build_layer.sh
./build_layer.sh --force
cd ../..

echo ""
echo "[2/5] CDK Bootstrap..."
cdk bootstrap

echo ""
echo "[3/5] CDK Deploy (all stacks)..."
cdk deploy --all --require-approval never --outputs-file cdk-outputs.json

echo ""
echo "[4/5] Extracting outputs..."
API_URL=$(python3 -c "
import json
d = json.load(open('cdk-outputs.json'))
for stack in d.values():
    for k, v in stack.items():
        if 'ApiUrl' in k or ('execute-api' in str(v) and v.endswith('/')):
            print(v)
            break
    else:
        continue
    break
")

FRONTEND_BUCKET=$(python3 -c "
import json
d = json.load(open('cdk-outputs.json'))
for stack in d.values():
    for k, v in stack.items():
        if 'FrontendBucketName' in k:
            print(v)
            break
    else:
        continue
    break
")

WEBSITE_URL=$(python3 -c "
import json
d = json.load(open('cdk-outputs.json'))
for stack in d.values():
    for k, v in stack.items():
        if 'WebsiteUrl' in k:
            print(v)
            break
    else:
        continue
    break
")

echo "  API URL: ${API_URL}"
echo "  Frontend Bucket: ${FRONTEND_BUCKET}"
echo "  Website URL: ${WEBSITE_URL}"

# Update config.js with actual API URL
sed -i.bak "s|PLACEHOLDER_API_URL|${API_URL}|g" frontend/js/config.js
rm -f frontend/js/config.js.bak

echo ""
echo "[5/5] Uploading frontend to S3..."
aws s3 sync frontend/ "s3://${FRONTEND_BUCKET}/" --delete

echo ""
echo "========================================="
echo "  Deploy Complete!"
echo "========================================="
echo "  Frontend: ${WEBSITE_URL}"
echo "  API:      ${API_URL}"
echo "========================================="
