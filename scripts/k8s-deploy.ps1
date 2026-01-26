#Requires -Version 5.1
<#
.SYNOPSIS
    Deploy the Todo Chatbot application to Minikube using Helm.

.DESCRIPTION
    This script deploys or upgrades the Todo Chatbot application using Helm.
    It requires a values-local.yaml file with secrets configured.

.EXAMPLE
    .\k8s-deploy.ps1
    Deploy the application (install or upgrade).

.EXAMPLE
    .\k8s-deploy.ps1 -DryRun
    Show what would be deployed without actually deploying.
#>

param(
    [Parameter()]
    [string]$ReleaseName = "todo",

    [Parameter()]
    [string]$Namespace = "default",

    [Parameter()]
    [switch]$DryRun,

    [Parameter()]
    [switch]$Install
)

$ErrorActionPreference = "Stop"

Write-Host "=== Todo Chatbot Helm Deployment Script ===" -ForegroundColor Cyan

# Get the project root directory
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path "$ProjectRoot\helm")) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}

$HelmChartPath = Join-Path $ProjectRoot "helm\todo-chatbot"
$ValuesLocalPath = Join-Path $HelmChartPath "values-local.yaml"

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Minikube
$minikubeStatus = minikube status --format='{{.Host}}' 2>$null
if ($minikubeStatus -ne "Running") {
    Write-Host "ERROR: Minikube is not running. Start it with: minikube start --memory=4096 --cpus=2" -ForegroundColor Red
    exit 1
}
Write-Host "  Minikube: Running" -ForegroundColor Green

# Check Helm
try {
    helm version --short | Out-Null
    Write-Host "  Helm: Installed" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Helm is not installed. Install with: winget install Helm.Helm" -ForegroundColor Red
    exit 1
}

# Check Helm chart exists
if (-not (Test-Path $HelmChartPath)) {
    Write-Host "ERROR: Helm chart not found at $HelmChartPath" -ForegroundColor Red
    exit 1
}
Write-Host "  Helm chart: Found" -ForegroundColor Green

# Check values-local.yaml exists
if (-not (Test-Path $ValuesLocalPath)) {
    Write-Host "ERROR: values-local.yaml not found. Copy and configure from values-local.yaml.example:" -ForegroundColor Red
    Write-Host "  cp $HelmChartPath\values-local.yaml.example $ValuesLocalPath" -ForegroundColor Yellow
    Write-Host "  notepad $ValuesLocalPath" -ForegroundColor Yellow
    exit 1
}
Write-Host "  values-local.yaml: Found" -ForegroundColor Green

# Check if Docker images exist
Write-Host "`nChecking Docker images..." -ForegroundColor Yellow
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

$frontendImage = docker images "todo-frontend:local" --format "{{.Repository}}:{{.Tag}}" 2>$null
$backendImage = docker images "todo-backend:local" --format "{{.Repository}}:{{.Tag}}" 2>$null

if (-not $frontendImage) {
    Write-Host "WARNING: todo-frontend:local image not found. Run .\k8s-build.ps1 first." -ForegroundColor Yellow
}
if (-not $backendImage) {
    Write-Host "WARNING: todo-backend:local image not found. Run .\k8s-build.ps1 first." -ForegroundColor Yellow
}

# Lint the chart
Write-Host "`nLinting Helm chart..." -ForegroundColor Yellow
helm lint $HelmChartPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Helm lint failed" -ForegroundColor Red
    exit 1
}

# Check if release exists
$existingRelease = helm list -n $Namespace --filter "^$ReleaseName$" --short 2>$null

# Deploy
Write-Host "`n--- Deploying to Kubernetes ---" -ForegroundColor Green

$helmArgs = @(
    "-n", $Namespace,
    "-f", $ValuesLocalPath
)

if ($DryRun) {
    $helmArgs += "--dry-run"
    Write-Host "(Dry run mode - no changes will be made)" -ForegroundColor Yellow
}

if ($existingRelease -and -not $Install) {
    Write-Host "Upgrading existing release: $ReleaseName"
    helm upgrade $ReleaseName $HelmChartPath @helmArgs
} else {
    Write-Host "Installing new release: $ReleaseName"
    helm install $ReleaseName $HelmChartPath @helmArgs
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Helm deployment failed" -ForegroundColor Red
    exit 1
}

if (-not $DryRun) {
    Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
    Write-Host "`nWaiting for pods to be ready..."

    # Wait for pods
    kubectl wait --for=condition=ready pod -l "app.kubernetes.io/instance=$ReleaseName" --timeout=120s -n $Namespace 2>$null

    Write-Host "`nPod Status:"
    kubectl get pods -l "app.kubernetes.io/instance=$ReleaseName" -n $Namespace

    Write-Host "`nService Status:"
    kubectl get services -l "app.kubernetes.io/instance=$ReleaseName" -n $Namespace

    Write-Host "`nAccess the application:"
    Write-Host "  Frontend: http://localhost:30080" -ForegroundColor Cyan
    Write-Host "  Or run: minikube service $ReleaseName-todo-chatbot-frontend --url" -ForegroundColor Gray
}
