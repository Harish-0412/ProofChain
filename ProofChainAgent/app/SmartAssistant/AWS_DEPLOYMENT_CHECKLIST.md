# AWS Deployment Checklist

Deployment is intentionally gated because AgentCore Runtime and Bedrock inference are usage-priced.

## Local Verification Completed

- Python tests pass.
- Telegram bot token is valid.
- Telegram chat allowlist is set.
- Advanced Telegram command keyboard works.
- `/center` Telegram smoke test succeeded.
- Telegram polling worker must be running or replaced by an AWS webhook bridge; AgentCore MCP deployment alone does not receive Telegram updates.
- Image ingestion stores photos locally and asks for user confirmation before inserting data.
- `/morning` live Gmail/Calendar digest works.
- `/emailplan` creates a confirmation-gated Calendar proposal from Gmail metadata.
- Google OAuth token exists.
- Google Calendar read API works.
- Gmail metadata read API works.
- CDK TypeScript build passes.
- CDK unit test passes.
- CDK synth passes after configuring `agentcore/aws-targets.json`.

## Current Deployment Blockers

- `aws sts get-caller-identity` must return your AWS account.
- `agentcore` must be available in the same shell PATH used for deployment.

Current target file is configured for:

```text
account=351405419703
region=ap-south-1
target=FacultyFlowMumbai
```

## Lowest-Cost Deployment Settings

Keep model usage capped:

```text
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
BEDROCK_MAX_TOKENS=350
FACULTYFLOW_ENABLE_BEDROCK=false
FACULTYFLOW_ENABLE_GOOGLE_WRITES=false
```

Only set this to `true` after the deployed endpoint is reachable:

```text
FACULTYFLOW_ENABLE_BEDROCK=true
```

## Safe Gate Commands

Run these before deploy:

```powershell
cd C:\SideQuest\ProofChain\ProofChainAgent
aws sts get-caller-identity
agentcore validate
cd agentcore\cdk
npm run build
npm run test -- --runInBand
npx cdk synth
```

Deploy only after synth passes:

```powershell
cd C:\SideQuest\ProofChain\ProofChainAgent
agentcore deploy
```

## Cost Notes

- AgentCore Runtime charges for active CPU and memory consumption.
- Bedrock model calls charge by model/provider token usage.
- CloudWatch logs may add small charges if log volume grows.
- Google and Telegram integrations should remain confirmation-gated for writes.
