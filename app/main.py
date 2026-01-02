from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import GenerateRequest, GenerateResponse
from .config import load_config
from .providers.azure_openai import AzureOpenAIProvider
from .providers.aws_bedrock import AwsBedrockProvider
from .cost_tracker import UsageLogger
from .router import run_generation
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="GenAI Cloud Gateway", version="1.0.0")

# CORS: adjust as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP_CFG, AZURE_CFG, BEDROCK_CFG = load_config()
usage_logger = UsageLogger(APP_CFG.log_db_path)

azure_provider = AzureOpenAIProvider(
    endpoint=AZURE_CFG.endpoint,
    api_key=AZURE_CFG.api_key,
    api_version=AZURE_CFG.api_version,
)
bedrock_provider = AwsBedrockProvider(region=BEDROCK_CFG.region)


@app.get("/health")
def health():
    return {"status": "ok", "env": APP_CFG.env}


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        result = run_generation(
            app_cfg=APP_CFG,
            azure_cfg=AZURE_CFG,
            bedrock_cfg=BEDROCK_CFG,
            req=req,
            azure_provider=azure_provider,
            bedrock_provider=bedrock_provider,
            usage_logger=usage_logger,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
