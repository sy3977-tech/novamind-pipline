# NovaMind AI Marketing Pipeline

An automated marketing pipeline that generates, distributes, and analyzes blog + newsletter content using Groq/Llama AI and HubSpot CRM. Built for NovaMind, a fictional AI startup helping creative agencies automate their workflows.

## Architecture & Flow

```
Topic Input (e.g. "AI in creative automation")
    ↓
[Step 1] content_generator.py
    → Groq/Llama generates blog post (400-600 words)
    → Generates 3 personalized newsletter versions (one per persona)
    → Saves to output/campaigns/content_TIMESTAMP.json
    ↓
[Step 2] crm_manager.py
    → Creates/updates mock contacts in HubSpot CRM
    → Segments contacts by persona
    → Logs campaign (title, newsletter, send date) as HubSpot notes
    → Saves to output/campaigns/crm_log_TIMESTAMP.json
    ↓
[Step 3] performance_tracker.py
    → Simulates realistic engagement metrics (open rate, click rate, unsubscribe rate)
    → Groq/Llama generates AI-powered performance summary + recommendations
    → Saves to output/campaigns/performance_TIMESTAMP.json
    ↓
[Step 4] optimizer.py  ← Bonus Feature
    → Suggests 5 next blog topics based on engagement trends
    → Generates 5 alternative headlines for A/B testing
    → Provides specific revision suggestions for lowest-performing newsletter
    → Saves to output/campaigns/optimization_TIMESTAMP.json
    ↓
[Dashboard] dashboard.py  ← Bonus Feature
    → Web UI at http://127.0.0.1:8080
    → View all results across 4 tabs: Overview, Content, Performance, AI Optimization
    → Trigger the full pipeline directly from the browser
```

## Personas Targeted

| Persona | Description |
|---|---|
| `creative_professional` | Freelance designers and creative directors at small agencies |
| `startup_founder` | Non-technical founders automating team workflows without engineers |
| `marketing_manager` | Marketing managers at mid-size companies exploring AI tools |

## Setup

### 1. Install dependencies
```bash
pip install groq python-dotenv requests flask
```

### 2. Configure `.env`
Create a `.env` file in the project root (see `.env.example` as template):
```
GROQ_API_KEY=your_groq_api_key_here
HUBSPOT_API_KEY=your_hubspot_private_app_token_here
```

Or copy from template:
```bash
cp .env.example .env
# Then edit .env with your actual API keys
```

**Getting a Groq API key (free):**
1. Go to https://console.groq.com and sign up
2. Click API Keys → Create API Key
3. Key starts with `gsk_`

**Getting a HubSpot API key (free developer account):**
1. Go to https://developers.hubspot.com and create a free account
2. Settings → Integrations → Private Apps → Create a private app
3. Required scope: `crm.objects.contacts.write`
4. Token starts with `pat-`

> Note: HubSpot key is optional. If not set, Step 2 is skipped and mock campaign data is used. All other steps work fully.

### 3. Run the full pipeline (terminal)
```bash
python main.py
```

### 4. Run the dashboard (browser UI)
```bash
python dashboard.py
```
Then open http://127.0.0.1:8080

### 5. Run individual steps
```bash
python content_generator.py    # Step 1 only
python crm_manager.py          # Step 2 only (needs content JSON first)
python performance_tracker.py  # Step 3 only (needs crm_log JSON first)
python optimizer.py            # Step 4 only (needs content + performance JSON)
```

## Output Files

All outputs saved in `output/campaigns/`:

| File | Description |
|---|---|
| `content_TIMESTAMP.json` | Generated blog post + 3 newsletter versions |
| `crm_log_TIMESTAMP.json` | HubSpot campaign log with contact IDs |
| `performance_TIMESTAMP.json` | Simulated metrics + AI summary report |
| `optimization_TIMESTAMP.json` | Topic suggestions + headlines + revision notes |

## Tools, APIs & Models Used

| Tool | Purpose |
|---|---|
| Groq API + Llama 3.3 70B | AI content generation and analysis |
| HubSpot CRM API v3 | Contact management and campaign logging |
| Flask | Web dashboard server |
| python-dotenv | Environment variable management |

## Assumptions

- Contact data is mocked (2 contacts per persona, 6 total)
- Newsletter "sending" is simulated — logged as HubSpot notes (no actual email delivery)
- Performance metrics (open rate, click rate, unsubscribe rate) are randomly generated within realistic industry benchmark ranges
- HubSpot free developer account is sufficient for all API calls used

## Troubleshooting

### `GroqError: The api_key client option must be set`

If you see this error, the `.env` file isn't being loaded properly:

**Solution 1: Set environment variable directly (recommended)**
```bash
export GROQ_API_KEY="your_api_key_here"
python main.py
```

**Solution 2: Verify `.env` file**
- Ensure `.env` is in the project root directory (same as `main.py`)
- File should contain: `GROQ_API_KEY=gsk_...`
- No spaces around `=`: ✅ `GROQ_API_KEY=value` ❌ `GROQ_API_KEY = value`

**Solution 3: Check file path**
If running from different directory:
```bash
cd /path/to/novamind-pipline
export GROQ_API_KEY="your_api_key_here"
python main.py
```

### Port 5000 / 8080 already in use

If dashboard fails with "Address already in use":
```bash
# On macOS / Linux: Kill the process using the port
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Then restart dashboard
python dashboard.py
```

### HubSpot authentication errors (non-critical)

If you see "Authentication credentials not found" when running Step 2:
- HubSpot integration is optional
- All other steps (content generation, performance analysis) still work
- Leave `HUBSPOT_API_KEY` blank or remove it from `.env`
