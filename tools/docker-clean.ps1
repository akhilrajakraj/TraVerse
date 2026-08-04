<#
===============================================================================
TraVerse Docker Cleanup Script
===============================================================================

Purpose:
    Safely clean Docker build cache without affecting:

    ✓ Running containers
    ✓ Docker images
    ✓ PostgreSQL volume
    ✓ Redis volume
    ✓ Development database

Recommended:
    Run once every week.

===============================================================================
#>

Clear-Host

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "        TraVerse Docker Cleanup"
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Current Docker disk usage..." -ForegroundColor Yellow
docker system df

Write-Host ""
Write-Host "Removing Docker Build Cache..." -ForegroundColor Green
docker builder prune -af

Write-Host ""
Write-Host "Removing stopped containers..." -ForegroundColor Green
docker container prune -f

Write-Host ""
Write-Host "Removing dangling images..." -ForegroundColor Green
docker image prune -f

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Docker disk usage after cleanup"
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

docker system df

Write-Host ""
Write-Host "[SUCCESS] Cleanup completed successfully." -ForegroundColor Green
Write-Host ""