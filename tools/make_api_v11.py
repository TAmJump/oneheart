#!/usr/bin/env python3
"""Build deploy/oneheart-api-v11.yaml from v10.

v11 differs from v10 in four ways:
  - the function code comes from an S3 zip instead of an inline ZipFile block
  - two tables are added: oneheart-certs and oneheart-payments
  - two routes are added: POST /verify and POST /square-webhook
  - the role may read the Square webhook signature key from SSM
"""
import io, sys

SRC = "/home/claude/oneheart/deploy/oneheart-api-v10.yaml"
DST = "/home/claude/oneheart/deploy/oneheart-api-v11.yaml"

lines = io.open(SRC, encoding="utf-8").read().split("\n")

# locate the inline code block: "      Code:" .. up to the line before "  Api:"
i_code = next(i for i, l in enumerate(lines) if l == "      Code:")
i_api = next(i for i, l in enumerate(lines) if l == "  Api:")
head = lines[:i_code]
tail = lines[i_api:]

s = "\n".join(head)

# ---- parameters -------------------------------------------------------------
s = s.replace(
    """  SquareTokenParam:
    Type: String
    Default: /oneheart/square/access-token
    Description: SSM SecureString parameter holding the Square production access token.
""",
    """  SquareTokenParam:
    Type: String
    Default: /oneheart/square/access-token
    Description: SSM SecureString parameter holding the Square production access token.
  SquareWebhookParam:
    Type: String
    Default: /oneheart/square/webhook-key
    Description: SSM SecureString parameter holding the Square webhook signature key. The webhook refuses every call until this parameter exists.
  SquareApplicationId:
    Type: String
    Default: sq0idp-DDvfI0E05acVUIYXHZimkQ
    Description: Square application id for ONE HEART. Webhook events from any other application are ignored.
  WebhookUrl:
    Type: String
    Default: https://7xw0uwnpra.execute-api.ap-northeast-1.amazonaws.com/square-webhook
    Description: The notification URL registered in the Square dashboard. Square signs the URL together with the body, so this must match exactly.
  CodeS3Bucket:
    Type: String
    Default: oneheart-deploy-310133718901
    Description: Bucket holding the function zip. Created once, outside this stack.
  CodeS3Key:
    Type: String
    Description: Key of the function zip. Change it on every deploy so the new code is picked up.
""")

# ---- new tables, inserted before PortraitsBucket ----------------------------
s = s.replace(
    "  PortraitsBucket:\n",
    """  CertsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: oneheart-certs
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - {AttributeName: certId, AttributeType: S}
      KeySchema:
        - {AttributeName: certId, KeyType: HASH}
      PointInTimeRecoverySpecification: {PointInTimeRecoveryEnabled: true}
      Tags:
        - {Key: project, Value: oneheart}

  PaymentsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: oneheart-payments
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - {AttributeName: paymentId, AttributeType: S}
      KeySchema:
        - {AttributeName: paymentId, KeyType: HASH}
      PointInTimeRecoverySpecification: {PointInTimeRecoveryEnabled: true}
      Tags:
        - {Key: project, Value: oneheart}

  PortraitsBucket:
""", 1)

# ---- role: new tables and the webhook parameter -----------------------------
s = s.replace(
    """                  - !GetAtt SignupsTable.Arn
                  - !GetAtt OrdersTable.Arn
                  - !GetAtt SlotsTable.Arn""",
    """                  - !GetAtt SignupsTable.Arn
                  - !GetAtt OrdersTable.Arn
                  - !GetAtt SlotsTable.Arn
                  - !GetAtt CertsTable.Arn
                  - !GetAtt PaymentsTable.Arn""")

s = s.replace(
    """              - Effect: Allow
                Action: [ssm:GetParameter]
                Resource: !Sub 'arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter${SquareTokenParam}'""",
    """              - Effect: Allow
                Action: [ssm:GetParameter]
                Resource:
                  - !Sub 'arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter${SquareTokenParam}'
                  - !Sub 'arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter${SquareWebhookParam}'""")

# ---- function environment ---------------------------------------------------
s = s.replace(
    """          SQ_LOCATION: !Ref SquareLocationId
          TOKEN_PARAM: !Ref SquareTokenParam""",
    """          SQ_LOCATION: !Ref SquareLocationId
          TOKEN_PARAM: !Ref SquareTokenParam
          CERTS: !Ref CertsTable
          PAYMENTS: !Ref PaymentsTable
          WEBHOOK_PARAM: !Ref SquareWebhookParam
          SQ_APP_ID: !Ref SquareApplicationId
          WEBHOOK_URL: !Ref WebhookUrl""")

# the webhook waits six seconds before it decides a payment is orphaned
s = s.replace("      Timeout: 20\n", "      Timeout: 25\n")

s = s.replace(
    "Description: ONE HEART PROJECT - participation backend (notify, place reservation, Square order, portrait storage)",
    "Description: ONE HEART PROJECT - participation backend (notify, place reservation, Square order, portrait storage, certificates, Square webhook). Code is deployed from an S3 zip; see tools/deploy_api.sh.")

# ---- code from S3 -----------------------------------------------------------
s += """\n      Code:
        S3Bucket: !Ref CodeS3Bucket
        S3Key: !Ref CodeS3Key

"""

t = "\n".join(tail)

# ---- new routes -------------------------------------------------------------
t = t.replace(
    """  RouteSlots:""",
    """  RouteVerify:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref Api
      RouteKey: 'POST /verify'
      Target: !Sub 'integrations/${Integration}'

  RouteSquareWebhook:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref Api
      RouteKey: 'POST /square-webhook'
      Target: !Sub 'integrations/${Integration}'

  RouteSlots:""")

t = t.replace(
    """  PortraitsBucketName:
    Value: !Ref PortraitsBucket""",
    """  PortraitsBucketName:
    Value: !Ref PortraitsBucket
  VerifyEndpoint:
    Value: !Sub 'https://${Api}.execute-api.${AWS::Region}.amazonaws.com/verify'
  SquareWebhookEndpoint:
    Description: Register this URL in the Square dashboard, and keep the WebhookUrl parameter identical to it.
    Value: !Sub 'https://${Api}.execute-api.${AWS::Region}.amazonaws.com/square-webhook'
  CertsTableName:
    Value: !Ref CertsTable
  PaymentsTableName:
    Value: !Ref PaymentsTable""")

io.open(DST, "w", encoding="utf-8").write(s + t)
print("wrote", DST, len(s + t), "bytes")
