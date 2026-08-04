<#
===============================================================================
TraVerse Docker FULL Cleanup

WARNING

This script removes:

✓ Build Cache
✓ Stopped Containers
✓ Unused Images
✓ Unused Networks

It DOES NOT remove Docker Volumes.

===============================================================================
#>

Clear-Host

Write-Host ""
Write-Host "=============================================" -ForegroundColor Red
Write-Host "        TraVerse FULL Docker Cleanup"
Write-Host "=============================================" -ForegroundColor Red
Write-Host ""

docker system df

Write-Host ""
Write-Host "Running Docker System Prune..." -ForegroundColor Yellow

docker system prune -af

Write-Host ""
Write-Host "Disk Usage After Cleanup"
Write-Host ""

docker system df

Write-Host ""
Write-Host "✓ Full cleanup complete." -ForegroundColor Green