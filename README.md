# GenAI Cloud Gateway

A **cloud-agnostic, cost-aware Generative AI gateway** that routes requests between **Azure OpenAI** and **AWS Bedrock** at runtime, providing a single, enterprise-ready API for GenAI workloads.

The project demonstrates **provider abstraction, cost optimisation, governance, and observability** — the exact concerns faced by large organisations adopting Generative AI.

---

## 🚀 Project Overview

Modern enterprises rarely standardise on a single GenAI provider. Regulatory constraints, cost control, latency, and resilience requirements often demand **multi-cloud AI strategies**.

**GenAI Cloud Gateway** solves this by providing:

- A **single REST API** for multiple GenAI providers
- **Dynamic routing** between Azure OpenAI and AWS Bedrock
- **Cost-aware model selection**
- **Centralised logging and auditability**
- **Extensible architecture** for additional providers and models

---

## 🎯 Key Capabilities

### ✅ Multi-Provider GenAI Routing
- Azure OpenAI (e.g. `gpt-4o-mini`)
- AWS Bedrock (Anthropic Claude models)
- Provider selection via:
  - request hints
  - cost/latency priority
  - fallback logic

### ✅ Cost Awareness
- Token estimation per request
- Per-provider cost modelling
- Persistent cost tracking in SQLite
- Enables downstream budgeting, alerts, and optimisation

### ✅ Enterprise-Ready Design
- Stateless API layer
- Externalised configuration via environment variables
- Explicit separation of provider adapters
- Clear extension points for governance and compliance

### ✅ Observability & Audit
- Every request logged with:
  - provider
  - model
  - estimated tokens
  - estimated cost
- SQLite used for simplicity (easily swappable for Postgres)

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  Client (curl/.NET/Postman)     │
└────────────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │  FastAPI Gateway    │
        │  /generate endpoint │
        └────────────┬────────┘
                     │
                     ▼
        ┌─────────────────────┐
        │  Routing Engine     │
        │  • priority         │
        │  • provider_hint    │
        │  • fallback logic   │
        └────────────┬────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   ┌──────────────┐      ┌──────────────────┐
   │ Azure OpenAI │      │  AWS Bedrock     │
   │   Adapter    │      │   Adapter        │
   └──────────────┘      └──────────────────┘
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────┐
        │ Usage & Cost Logging│
        │ SQLite (usage_logs) │
        └─────────────────────┘
```



---

## 🧪 Supported Tasks

The gateway is **task-driven**, not model-driven.

Current tasks:
- `chat` – conversational responses
- `summarise` – text summarisation

(Adding tasks such as `extract`, `classify`, `rewrite` is trivial.)

---

## 📦 Tech Stack

### Backend
- **Python 3.11**
- **FastAPI**
- **Uvicorn**
- **Pydantic**

### Cloud Providers
- **Azure OpenAI Service**
- **AWS Bedrock (Anthropic Claude)**

### Client / Integration
- **curl**
- **.NET 8 client (C#)**

### Persistence
- **SQLite** (for portability and demo simplicity)

### DevOps
- **Docker**
- Environment-driven configuration
- Designed for CI/CD pipelines

---

## ⚙️ Configuration

All configuration is done via `.env`.

### Azure OpenAI

```
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_KEY=xxxxxxxx
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### AWS Bedrock
```
AWS_PROFILE=bedrock
AWS_REGION=eu-west-2
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```


## 📁 Project File Structure
```
genai-cloud-gateway/
│
├── app/                                # Core FastAPI application
│   ├── __pycache__/                    # Python bytecode cache
│   │
│   ├── providers/                     # GenAI provider adapters
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── base.py                    # Abstract provider interface
│   │   ├── azure_openai.py            # Azure OpenAI implementation
│   │   └── aws_bedrock.py             # AWS Bedrock implementation
│   │
│   ├── __init__.py
│   ├── config.py                     # Environment & runtime configuration
│   ├── cost_tracker.py               # Token & cost estimation + persistence
│   ├── main.py                       # FastAPI entry point
│   ├── models.py                     # Pydantic request/response models
│   └── router.py                     # Provider selection & routing logic
│
├── clients/
│   └── dotnet-client/                # Example enterprise client (.NET)
│       ├── bin/                      # Build output (ignored in VCS)
│       ├── obj/                      # Build intermediates (ignored in VCS)
│       ├── DotNetClient.csproj       # .NET project definition
│       └── Program.cs                # Console client entry point
│
├── docker/
│   └── Dockerfile                    # Container build definition
│
├── scripts/                          # Operational & diagnostic scripts
│   ├── bedrock_body.json             # Sample AWS Bedrock request payload
│   ├── bedrock_smoke_test.ps1        # Bedrock connectivity smoke test
│   ├── fix_bom.py                    # Utility to fix BOM / encoding issues
│   └── load-env.ps1                  # Helper to load .env into PowerShell
│
├── venv/                             # Python virtual environment (local only)
│
├── .env                              # Local environment variables (ignored)
├── .env.example                      # Example environment configuration
├── body.json                         # Generic request payload example
├── genai-cloud-gateway.sln           # Visual Studio solution file
├── NuGet.Config                      # NuGet configuration (fallback fix)
├── requirements.txt                  # Python dependencies
├── usage_logs.sqlite                 # Usage & cost audit database
├── README.md                         # Project documentation
└── my.notes.txt                      # Local development notes (optional)

```

## 🧠 Structure Rationale 
 - app/providers enforces a clean provider abstraction layer, preventing vendor lock-in
 - router.py centralises decision logic (priority, hints, fallback)
 - cost_tracker.py makes cost a first-class concern, not an afterthought
 - clients/dotnet-client demonstrates real enterprise integration, not toy usage
 - scripts/ mirrors real ops workflows: smoke tests, encoding fixes, env bootstrapping
 - SQLite is used intentionally for auditability and portability, with a clear upgrade path to Postgres

## ✅ Why this structure works well for recruiters

This layout clearly demonstrates:
 - separation of concerns
 - extensibility
 - operational awareness
 - multi-cloud GenAI maturity


## ▶️ Running the API (Local)

### 1. Create virtual environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```


### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Start the server
```
uvicorn app.main:app --reload --port 8000
```

API will be available at:
```
http://localhost:8000
```

## Example Requests
### Simple chat request
```
  curl.exe -X POST http://localhost:8000/generate `
  -H "Content-Type: application/json" `
  -d "{\"prompt\":\"Hello\",\"task\":\"chat\",\"priority\":\"low_cost\"}"
```
### Force AWS Bedrock
```
curl.exe -X POST http://localhost:8000/generate `
  -H "Content-Type: application/json" `
  -d "{\"prompt\":\"Hello from Bedrock\",\"task\":\"chat\",\"provider_hint\":\"bedrock\"}"
```

## 📊 Inspecting Usage & Cost Logs
The gateway writes all usage to:
```
usage_logs.sqlite

```
Example query:
```
SELECT provider, model, total_tokens_est, cost_est_usd
FROM usage_logs
ORDER BY id DESC
LIMIT 10;
```

This enables:
- per-provider cost analysis
- audit trails
- chargeback modelling


## 🧰 .NET Client
A simple .NET 8 console client is included to demonstrate enterprise integration patterns.

Build and run:
```
dotnet build .\clients\dotnet-client\DotNetClient.csproj
dotnet run --project .\clients\dotnet-client http://localhost:8000
```


## 🐳 Docker
### Build image
```
docker build -t genai-cloud-gateway -f docker/Dockerfile .
```
### Run container
```
docker run --rm -p 8000:8000 --env-file .env genai-cloud-gateway
```

## 🔐 Security & Governance Considerations

This project is intentionally designed to support:
- Provider abstraction (avoid vendor lock-in)
- Auditability (who used what, at what cost)
- Policy enforcement points
- Data residency strategies
- Ethical AI & cost controls

These are critical for:
- government
- financial services
- regulated enterprises


## 🧠 Why This Project Matters

Most GenAI demos:
- hard-code a single provider
- ignore cost
- lack observability
- collapse under enterprise scrutiny

This gateway reflects real-world GenAI platform engineering:
- multi-cloud
- cost-aware
- auditable
- extensible


## 🔮 Future Enhancements

- PostgreSQL backend
- OpenTelemetry metrics
- Rate limiting & quotas
- RAG support (Azure Search / OpenSearch)
- Policy-based routing (OPA)
- Fine-grained cost dashboards

## 👤 Author

#### Samuel Aina
AI / LLM Architect & Consultant

Specialising in:
- Enterprise GenAI
- Multi-cloud AI platforms
- Secure, cost-aware AI solutions

## 📄 License
MIT License


