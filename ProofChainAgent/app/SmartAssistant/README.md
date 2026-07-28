# FacultyFlow Local MVP

FacultyFlow is a local-first academic work-planning MCP server. This MVP uses mock calendar, email, task, and preference data so you can test planning quality without spending AWS credits.

## What Works Now

- Introduces the FacultyFlow agent.
- Reads mock calendar events.
- Reads mock actionable email summaries.
- Reads mock pending tasks.
- Handles Telegram commands through a local long-polling bot adapter.
- Provides guarded Bedrock integration that is disabled by default.
- Provides Google Workspace integration scaffolding for Gmail/Calendar OAuth.
- Builds a prioritized daily plan.
- Detects schedule conflicts and deadline risks.
- Suggests focus blocks and postponements.
- Creates draft-only calendar and email proposals.
- Lists Telegram setup requirements for the later integration phase.

## Cost Guardrail

This local MVP does not call Amazon Bedrock, deploy AgentCore Runtime, create DynamoDB tables, call Gmail, call Google Calendar, or send Telegram messages.

Telegram polling will call Telegram only when you explicitly run `telegram_bot.py`. Bedrock remains off unless `FACULTYFLOW_ENABLE_BEDROCK=true`.

Do not run these commands until you explicitly want AWS resources:

```powershell
agentcore deploy
aws cloudformation deploy
cdk deploy
```

## Local Development

From this folder:

```powershell
uv sync
uv run python main.py
```

From the AgentCore project root, MCP tools are invoked with the AgentCore MCP command style:

```powershell
cd C:\SideQuest\ProofChain\ProofChainAgent
agentcore dev
agentcore dev list-tools
agentcore dev call-tool --tool introduce
agentcore dev call-tool --tool plan_my_day
agentcore dev call-tool --tool telegram_setup_requirements
```

If your installed CLI requires arguments, check:

```powershell
agentcore dev call-tool --help
```

## MCP Tools

| Tool | Purpose |
| --- | --- |
| `introduce` | Explains what FacultyFlow can do locally. |
| `plan_my_day` | Creates a daily plan using mock data. |
| `get_today_schedule` | Returns mock calendar events. |
| `get_tasks` | Returns mock tasks by status. |
| `list_actionable_emails` | Returns safe email summaries only. |
| `propose_calendar_event` | Creates a draft calendar proposal only. |
| `draft_email` | Creates a draft email only. |
| `telegram_setup_requirements` | Lists data needed before connecting Telegram. |

## Telegram Information Needed Later

When you are ready to connect Telegram, collect these but do not commit them:

- Telegram bot token from BotFather.
- Your numeric Telegram chat ID or a list of allowed user IDs.
- Commands to enable first, such as `/today`, `/plan`, `/tasks`, and `/help`.
- Whether this is a personal-only bot or a multi-user bot.
- Morning briefing time and timezone.
- Confirmation policy for write actions. Recommended: always ask.

Secrets should go into `agentcore/.env.local` locally or AWS Secrets Manager after deployment.

## Run Telegram Locally

Set these in `agentcore/.env.local`:

```text
TELEGRAM_BOT_TOKEN=<your BotFather token>
TELEGRAM_ALLOWED_CHAT_IDS=<your numeric chat id>
TELEGRAM_ALLOW_ALL_CHATS=false
FACULTYFLOW_ENABLE_BEDROCK=false
```

Then run:

```powershell
uv run python telegram_bot.py
```

Use `/start`, `/today`, `/calendar`, `/emails`, `/tasks`, `/google`, and `/cost`.

Advanced teacher workflow commands:

```text
/center
/brief
/radar
/meetings
/live
/morning
/emailplan
/draftemail
/imagehelp
/automate
/pending
/state
/google_calendar
/gmail
/draftmail recipient@example.com | Subject | Purpose text
/focusdraft Title | 2026-07-28T10:00:00 | 2026-07-28T10:45:00 | Reason
/confirm pending-0001
/cancel pending-0001
/addtask Prepare quiz | deadline=2026-07-28T15:00:00 | minutes=30 | importance=4
/ingest task: Finish lab manual | deadline=2026-07-28T16:00:00 | minutes=45 | importance=4 | category=Reports
/ingest event: DBMS class | date=2026-07-28 | start=10:00 | end=11:00 | category=class
/ingest email: hod@college.edu | subject=Report needed | due=14:00 | urgency=critical | summary=Submit IA report
/ingest pref: preferred_focus_minutes=45
```

Use `/ingest` without arguments to display the accepted import format.

The bot sends a persistent command keyboard with descriptive buttons such as:

```text
Center - dashboard
Brief - quick view
Plan - full day
Radar - risks
Meetings - prep
Live - Google
Morning - 6AM brief
EmailPlan - followups
Images - timetable
Ingest - add data
Pending - approvals
Cost - safety
```

The Telegram slash-command menu is also registered with short descriptions. Slow commands show a typing indicator and send a short working note before doing Gmail/Calendar work.

Image ingestion:

- Send a timetable, meeting notice, circular, or task screenshot as a Telegram photo.
- Add a caption if possible, for example `type=timetable date=2026-07-29 note=AI lab slots`.
- FacultyFlow saves the image and creates a pending review item.
- Nothing is inserted into your timetable until you confirm the exact extracted details in text.

Morning digest:

- The polling worker sends one digest per day after 6:00 AM IST when it is running.
- Use `/morning` to trigger the same digest manually.
- The digest reads Calendar and Gmail metadata, lists unread/important messages, and suggests next actions.

Gmail to Calendar:

- Use `/emailplan` to create a confirmation-gated calendar proposal for reviewing important/unread emails.
- Use `/pending` to inspect proposals.
- Use `/confirm <id>` only after checking the proposed title/time/reason.
- Real Google writes require `FACULTYFLOW_ENABLE_GOOGLE_WRITES=true`; it is disabled by default.

Gmail draft assistant:

- Use `/draftemail` or the `DraftEmail - gmail` button.
- FacultyFlow asks for recipient, subject, and a short purpose.
- It then creates a ready-to-review draft in Gmail Drafts when OAuth includes `gmail.compose`.
- If `gmail.compose` is missing, rerun:

```powershell
uv run python google_oauth.py
```

Approve the updated Gmail permissions, then try `/draftemail` again.

## Bedrock

The project is configured for Amazon Nova Micro first because it is Amazon's fastest text-only low-cost model. Keep it disabled until you explicitly want live inference:

```text
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
BEDROCK_MAX_TOKENS=350
FACULTYFLOW_ENABLE_BEDROCK=false
FACULTYFLOW_ENABLE_GOOGLE_WRITES=false
```

Keep Google writes disabled until you intentionally want `/confirm <id>` to create real calendar events or send real Gmail messages.

## Gmail And Calendar

Real Gmail/Calendar access requires Google OAuth consent. Telegram credentials cannot grant Google access.

Your current client secret is a Google OAuth **Web application** client. For local testing, add this exact Authorized redirect URI in Google Cloud Console:

```text
http://localhost:8765/
```

Then run:

```powershell
uv run python google_oauth.py
```

Alternative: create a Google OAuth **Desktop app** client and replace `GOOGLE_OAUTH_CLIENT_SECRET_FILE` with that JSON file.

Recommended first scopes:

```text
https://www.googleapis.com/auth/calendar.events.readonly
https://www.googleapis.com/auth/gmail.metadata
```

Write scopes should be enabled only after confirmation workflow testing:

```text
https://www.googleapis.com/auth/calendar.events
https://www.googleapis.com/auth/gmail.send
```

## Mock Data

Edit these files to tune the MVP:

- `data/mock_calendar.json`
- `data/mock_emails.json`
- `data/mock_tasks.json`
- `data/preferences.json`
