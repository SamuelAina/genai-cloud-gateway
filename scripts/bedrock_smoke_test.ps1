# scripts/bedrock_smoke_test.ps1
# Bedrock smoke test: invokes a model via AWS CLI using a file:// body.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\bedrock_smoke_test.ps1
# Optional:
#   $env:AWS_PROFILE="bedrock"  # if using a named profile

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Load-DotEnvIfPresent {
    param([string]$EnvPath)

    if (-not (Test-Path $EnvPath)) {
        Write-Host "No .env found at $EnvPath (skipping .env load)." -ForegroundColor Yellow
        return
    }

    Write-Host "Loading environment from $EnvPath ..." -ForegroundColor Cyan
    $lines = Get-Content $EnvPath

    foreach ($line in $lines) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$") { continue }

        $kv = $line.Split("=", 2)
        if ($kv.Count -lt 2) { continue }

        $name = $kv[0].Trim()
        $value = $kv[1].Trim()
        # Remove trailing inline comments like: VALUE # comment
        if ($value -match "^(.*?)(\s+#.*)$") {
            $value = $Matches[1].Trim()
        }

        # Strip optional surrounding quotes
        if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }
        if ($value.StartsWith("'") -and $value.EndsWith("'")) { $value = $value.Trim("'") }

        [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
    }

    Write-Host "Loaded .env into this PowerShell session." -ForegroundColor Green
}

function Require-Command {
    param([string]$Cmd)

    $found = Get-Command $Cmd -ErrorAction SilentlyContinue
    if (-not $found) {
        throw "Required command not found: $Cmd. Install AWS CLI v2 and ensure it's on PATH."
    }
}

# --- Main ---
try {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $envPath = Join-Path $repoRoot ".env"

    Load-DotEnvIfPresent -EnvPath $envPath
    Require-Command -Cmd "aws"

    Write-Host "*********" -ForegroundColor Cyan
    Write-Host $env:BEDROCK_MODEL_LOW_COST -ForegroundColor Red
    Write-Host "*********" -ForegroundColor Cyan

    # Pick region/model from env if present, else fall back to sensible defaults
    $region = if ($env:AWS_REGION) { $env:AWS_REGION } else { "eu-west-2" }
    $modelId = if ($env:BEDROCK_MODEL_LOW_COST) { $env:BEDROCK_MODEL_LOW_COST } else { "anthropic.claude-3-haiku-20240307-v1:0" }

    Write-Host "Using AWS region: $region" -ForegroundColor Cyan
    Write-Host "Using Bedrock model: $modelId" -ForegroundColor Cyan

    # Ensure the script directory exists for temp files
    $scriptDir = $PSScriptRoot
    if (-not (Test-Path $scriptDir)) {
        New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
    }

    # Write request body
    $bodyPath = Join-Path $scriptDir "bedrock_body.json"
    $responsePath = Join-Path $scriptDir "bedrock_response.json"

    $body = @{
        anthropic_version = "bedrock-2023-05-31"
        messages = @(
            @{
                role = "user"
                content = @(
                    @{ 
                        type = "text"
                        text = "Hello. Reply with: Bedrock smoke test OK." 
                    }
                )
            }
        )
        max_tokens = 64
        temperature = 0.2
        top_p = 0.9
    }

    $body | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $bodyPath
    Write-Host "Wrote request body: $bodyPath" -ForegroundColor Green

    # Convert Windows path to file:// URL format
    $fileUrl = "file://" + ($bodyPath -replace '\\', '/')
    Write-Host "Using file URL: $fileUrl" -ForegroundColor Cyan

    # Invoke model
    Write-Host "Invoking Bedrock..." -ForegroundColor Cyan

    # Clean up any existing response file
    if (Test-Path $responsePath) {
        Remove-Item $responsePath -Force -ErrorAction SilentlyContinue
    }

    # Build the AWS CLI command as a string for debugging
    $awsCmd = "aws bedrock-runtime invoke-model " +
              "--model-id `"$modelId`" " +
              "--content-type `"application/json`" " +
              "--accept `"application/json`" " +
              "--body `"$fileUrl`" " +
              "--cli-binary-format `"raw-in-base64-out`" " +
              "`"$responsePath`" " +
              "--region `"$region`""
    
    Write-Host "Running command:" -ForegroundColor Cyan
    Write-Host $awsCmd -ForegroundColor DarkGray

    # Execute the command
    Invoke-Expression $awsCmd
    
    # Check for errors
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI failed with exit code $LASTEXITCODE"
    }

    Write-Host "Wrote response: $responsePath" -ForegroundColor Green

    # Check if response file exists and has content
    if (-not (Test-Path $responsePath)) {
        throw "Response file was not created: $responsePath"
    }

    $responseContent = Get-Content $responsePath -Raw -ErrorAction Stop
    if ([string]::IsNullOrWhiteSpace($responseContent)) {
        throw "Response file is empty: $responsePath"
    }

    # Parse and display response
    try {
        $respJson = $responseContent | ConvertFrom-Json
        $text = $null

        # Handle Claude 3 response format
        if ($respJson.content -and $respJson.content.Count -gt 0) {
            $text = $respJson.content[0].text
        }
        # Handle Claude 2/other Anthropic completion format
        elseif ($respJson.completion) {
            $text = $respJson.completion
        }

        if ($text) {
            Write-Host "`n--- Model Output ---" -ForegroundColor Magenta
            Write-Host $text
            Write-Host "--------------------`n" -ForegroundColor Magenta
        }
        else {
            Write-Host "Response JSON did not contain expected 'content[0].text' or 'completion'. Showing raw JSON:" -ForegroundColor Yellow
            Write-Host ($respJson | ConvertTo-Json -Depth 10)
        }
    }
    catch {
        Write-Host "Could not parse response as JSON. Dumping file contents:" -ForegroundColor Yellow
        Write-Host $responseContent
    }

    Write-Host "Bedrock smoke test completed successfully." -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "`nERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Error occurred at line: $($_.InvocationInfo.ScriptLineNumber)" -ForegroundColor Red
    Write-Host "In command: $($_.InvocationInfo.Line)" -ForegroundColor Red
    
    if ($_.Exception.InnerException) {
        Write-Host "Inner exception: $($_.Exception.InnerException.Message)" -ForegroundColor Red
    }
    
    exit 1
}