# Deployment Guardrails

This project must stay low-cost by default.

## Cost Facts

- Amazon Bedrock model inference is usage-priced by provider/model.
- Amazon Bedrock AgentCore Runtime is consumption-priced by active CPU and memory.
- AgentCore Gateway, Memory, Observability, and Web Search can add charges.
- AWS Free Tier credits may cover early usage for eligible new accounts, but that is not the same as a permanently free model.

## Selected Low-Cost Model

Use Amazon Nova Micro first:

```text
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
AWS_REGION=ap-south-1
BEDROCK_MAX_TOKENS=350
FACULTYFLOW_ENABLE_BEDROCK=false
```

Keep `FACULTYFLOW_ENABLE_BEDROCK=false` until you are ready to pay for live inference.

## Deployment Rules

1. Test locally with mock data.
2. Connect Telegram locally with long polling.
3. Complete Google OAuth locally.
4. Enable Bedrock with low token caps.
5. Deploy only after confirming expected AWS costs.
6. Keep all write actions confirmation-gated.

## Commands That May Create Costs

```powershell
agentcore deploy
cdk deploy
aws cloudformation deploy
aws bedrock-runtime converse
```

## Google Access Required Later

Telegram does not grant Gmail or Calendar access. You must configure Google OAuth.

For the local OAuth helper, use either:

- a Web application client with `http://localhost:8765/` added under Authorized redirect URIs, or
- a Desktop app OAuth client JSON.

Recommended minimal scopes:

```text
https://www.googleapis.com/auth/calendar.events.readonly
https://www.googleapis.com/auth/gmail.metadata
```

For confirmed writes only:

```text
https://www.googleapis.com/auth/calendar.events
https://www.googleapis.com/auth/gmail.send
```
