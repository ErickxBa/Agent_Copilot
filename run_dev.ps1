# Script de inicio rápido para Agent_Banca (Frontend + Backend)
param (
    [string]$Service = "both"
)

Write-Host "🏦 Agent_Banca FinTech Platform Starter" -ForegroundColor Cyan

if ($Service -eq "backend" -or $Service -eq "both") {
    Write-Host "Iniciando FastAPI Backend en http://127.0.0.1:8000 ..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn src.api_server:app --host 127.0.0.1 --port 8000 --reload"
}

if ($Service -eq "frontend" -or $Service -eq "both") {
    Write-Host "Iniciando Vite React Frontend en http://localhost:5173 ..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
}

Write-Host "¡Servicios lanzados! Revisa las ventanas de terminal abiertas." -ForegroundColor Cyan

