#Requires -Version 5.1
<#
.SYNOPSIS
    Build Docker images for the Todo Chatbot application inside Minikube.

.DESCRIPTION
    This script configures the Docker environment to use Minikube's Docker daemon
    and builds both frontend and backend Docker images.

.EXAMPLE
    .\k8s-build.ps1
    Build both frontend and backend images.

.EXAMPLE
    .\k8s-build.ps1 -Component frontend
    Build only the frontend image.
#>

param(
    [Parameter()]
    [ValidateSet("all", "frontend", "backend")]
    [string]$Component = "all",

    [Parameter()]
    [string]$Tag = "local"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Todo Chatbot Docker Build Script ===" -ForegroundColor Cyan

# Check if Minikube is running
$minikubeStatus = minikube status --format='{{.Host}}' 2>$null
if ($minikubeStatus -ne "Running") {
    Write-Host "ERROR: Minikube is not running. Start it with: minikube start --memory=4096 --cpus=2" -ForegroundColor Red
    exit 1
}

# Configure Docker environment for Minikube
Write-Host "Configuring Docker environment for Minikube..." -ForegroundColor Yellow
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Get the project root directory
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path "$ProjectRoot\frontend")) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}

Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray

function Build-FrontendImage {
    Write-Host "`n--- Building Frontend Image ---" -ForegroundColor Green

    $frontendPath = Join-Path $ProjectRoot "frontend"
    if (-not (Test-Path $frontendPath)) {
        Write-Host "ERROR: Frontend directory not found at $frontendPath" -ForegroundColor Red
        return $false
    }

    # NEXT_PUBLIC_* vars must be set at build time for Next.js
    # These URLs are what the browser will use to connect
    $buildArgs = @(
        "--build-arg", "NEXT_PUBLIC_APP_NAME=Todo App (K8s Local)",
        "--build-arg", "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000",
        "--build-arg", "NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000"
    )

    # Add OpenAI domain key if available from values-local.yaml
    $valuesLocalPath = Join-Path $ProjectRoot "helm\todo-chatbot\values-local.yaml"
    if (Test-Path $valuesLocalPath) {
        $content = Get-Content $valuesLocalPath -Raw
        if ($content -match 'openaiDomainKey:\s*"([^"]+)"') {
            $domainKey = $matches[1]
            $buildArgs += @("--build-arg", "NEXT_PUBLIC_OPENAI_DOMAIN_KEY=$domainKey")
            Write-Host "Using OpenAI domain key from values-local.yaml" -ForegroundColor Gray
        }
    }

    Write-Host "Building todo-frontend:$Tag..."
    docker build @buildArgs -t "todo-frontend:$Tag" $frontendPath

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend build failed" -ForegroundColor Red
        return $false
    }

    # Check image size
    $imageSize = docker images "todo-frontend:$Tag" --format "{{.Size}}"
    Write-Host "Frontend image size: $imageSize" -ForegroundColor Gray

    return $true
}

function Build-BackendImage {
    Write-Host "`n--- Building Backend Image ---" -ForegroundColor Green

    $backendPath = Join-Path $ProjectRoot "backend"
    if (-not (Test-Path $backendPath)) {
        Write-Host "ERROR: Backend directory not found at $backendPath" -ForegroundColor Red
        return $false
    }

    Write-Host "Building todo-backend:$Tag..."
    docker build -t "todo-backend:$Tag" $backendPath

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Backend build failed" -ForegroundColor Red
        return $false
    }

    # Check image size
    $imageSize = docker images "todo-backend:$Tag" --format "{{.Size}}"
    Write-Host "Backend image size: $imageSize" -ForegroundColor Gray

    return $true
}

# Build based on component selection
$success = $true

switch ($Component) {
    "frontend" {
        $success = Build-FrontendImage
    }
    "backend" {
        $success = Build-BackendImage
    }
    "all" {
        $frontendSuccess = Build-FrontendImage
        $backendSuccess = Build-BackendImage
        $success = $frontendSuccess -and $backendSuccess
    }
}

if ($success) {
    Write-Host "`n=== Build Complete ===" -ForegroundColor Green
    Write-Host "Images available in Minikube Docker:"
    docker images | Select-String "todo-"
} else {
    Write-Host "`n=== Build Failed ===" -ForegroundColor Red
    exit 1
}
