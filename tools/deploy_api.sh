#!/usr/bin/env bash
# ONE HEART - deploy the participation API.
#
# From v11 the function code is no longer carried inside the CloudFormation
# template. This script downloads lambda/index.js and the template, packs the
# code into a zip, puts the zip in the deploy bucket under a key that changes
# with the code, and updates the stack.
#
#   bash deploy_api.sh              # deploy the head of main
#   bash deploy_api.sh <commit>     # deploy one exact commit (never cached)
#
# Run it in CloudShell in ap-northeast-1.

set -euo pipefail

REPO=TAmJump/oneheart
REF="${1:-main}"
TEMPLATE=oneheart-api-v11.yaml
STACK=oneheart-api
REGION=ap-northeast-1
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="oneheart-deploy-${ACCOUNT}"

echo "repo     ${REPO}@${REF}"
echo "account  ${ACCOUNT}"
echo "bucket   ${BUCKET}"
echo

RAW="https://raw.githubusercontent.com/${REPO}/${REF}"
curl -fsSL "${RAW}/lambda/index.js"        -o "${WORK}/index.js"
curl -fsSL "${RAW}/deploy/${TEMPLATE}"     -o "${WORK}/${TEMPLATE}"

if command -v node >/dev/null 2>&1; then
  node --check "${WORK}/index.js"
  echo "code     $(wc -c < "${WORK}/index.js") bytes, syntax ok"
else
  echo "code     $(wc -c < "${WORK}/index.js") bytes (no node here, syntax not checked)"
fi

SHA="$(sha256sum "${WORK}/index.js" | cut -c1-12)"
KEY="lambda/oneheart-api-${SHA}.zip"

python3 - "$WORK" <<'PY'
import sys, zipfile, os
w = sys.argv[1]
with zipfile.ZipFile(os.path.join(w, "code.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(w, "index.js"), "index.js")
PY

if ! aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
  echo "creating ${BUCKET}"
  aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" \
    --create-bucket-configuration LocationConstraint="${REGION}" >/dev/null
  aws s3api put-public-access-block --bucket "${BUCKET}" \
    --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-versioning --bucket "${BUCKET}" \
    --versioning-configuration Status=Enabled
fi

aws s3 cp "${WORK}/code.zip" "s3://${BUCKET}/${KEY}" --region "${REGION}"
echo "zip      s3://${BUCKET}/${KEY}"
echo

aws cloudformation deploy \
  --stack-name "${STACK}" \
  --template-file "${WORK}/${TEMPLATE}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "${REGION}" \
  --parameter-overrides "CodeS3Bucket=${BUCKET}" "CodeS3Key=${KEY}"

echo
aws cloudformation describe-stacks --stack-name "${STACK}" --region "${REGION}" \
  --query 'Stacks[0].Outputs[?OutputKey==`SquareWebhookEndpoint`||OutputKey==`VerifyEndpoint`].[OutputKey,OutputValue]' \
  --output text
