#Requires -Version 5.1
<#
.SYNOPSIS
    Tear down the Todo Chatbot deployment from Minikube.

.DESCRIPTION
    This script uninstalls the Helm release and optionally stops/deletes Minikube.

.EXAMPLE
    .\k8s-teardown.ps1
    Uninstall the Helm release only.

.EXAMPLE
    .\k8s-teardown.ps1 -StopMinikube
    Uninstall the release and stop Minikube.

.EXAMPLE
    .\k8s-teardown.ps1 -DeleteMinikube
    Uninstall the release and delete the Minikube cluster.
#>

param(
    [Parameter()]
    [string]$ReleaseName = "todo",

    [Parameter()]
    [string]$Namespace = "default",

    [Parameter()]
    [switch]$StopMinikube,

    [Parameter()]
    [switch]$DeleteMinikube,

    [Parameter()]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "=== Todo Chatbot Teardown Script ===" -ForegroundColor Cyan

# Check if Minikube is running
$minikubeStatus = minikube status --format='{{.Host}}' 2>$null

if ($minikubeStatus -eq "Running") {
    # Check if release exists
    $existingRelease = helm list -n $Namespace --filter "^$ReleaseName$" --short 2>$null

    if ($existingRelease) {
        if (-not $Force) {
            $confirm = Read-Host "Are you sure you want to uninstall release '$ReleaseName'? (y/N)"
            if ($confirm -ne "y" -and $confirm -ne "Y") {
                Write-Host "Cancelled." -ForegroundColor Yellow
                exit 0
            }
        }

        Write-Host "Uninstalling Helm release: $ReleaseName" -ForegroundColor Yellow
        helm uninstall $ReleaseName -n $Namespace

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Release '$ReleaseName' uninstalled successfully." -ForegroundColor Green
        } else {
            Write-Host "WARNING: Failed to uninstall release" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Release '$ReleaseName' not found in namespace '$Namespace'." -ForegroundColor Yellow
    }

    # Optionally remove Docker images
    Write-Host "`nDocker images (not removed):" -ForegroundColor Gray
    & minikube -p minikube docker-env --shell powershell | Invoke-Expression
    docker images | Select-String "todo-"
    Write-Host "To remove images: docker rmi todo-frontend:local todo-backend:local" -ForegroundColor Gray
}

if ($StopMinikube -or $DeleteMinikube) {
    if ($minikubeStatus -eq "Running") {
        Write-Host "`nStopping Minikube..." -ForegroundColor Yellow
        minikube stop

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Minikube stopped." -ForegroundColor Green
        }
    } else {
        Write-Host "Minikube is not running." -ForegroundColor Gray
    }
}

if ($DeleteMinikube) {
    if (-not $Force) {
        $confirm = Read-Host "Are you sure you want to DELETE the Minikube cluster? This cannot be undone. (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "Cancelled." -ForegroundColor Yellow
            exit 0
        }
    }

    Write-Host "`nDeleting Minikube cluster..." -ForegroundColor Red
    minikube delete

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Minikube cluster deleted." -ForegroundColor Green
    }
}

Write-Host "`n=== Teardown Complete ===" -ForegroundColor Green
