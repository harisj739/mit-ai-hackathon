#!/usr/bin/env python3
"""
Simple standalone dashboard test
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn

# Create FastAPI app
app = FastAPI(title="FailProof LLM Dashboard")

# Setup static files and templates
dashboard_dir = Path("src/dashboard")
if dashboard_dir.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_dir / "static")), name="static")
    if (dashboard_dir / "templates").exists():
        templates = Jinja2Templates(directory=str(dashboard_dir / "templates"))
    else:
        templates = None
else:
    templates = None

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        return """
        <html>
        <head><title>FailProof LLM Dashboard</title></head>
        <body>
            <h1>FailProof LLM Dashboard</h1>
            <p>Templates not found. Dashboard files should be in src/dashboard/</p>
        </body>
        </html>
        """

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Dashboard is running"}

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics."""
    return {
        "total_test_runs": 42,
        "total_test_cases": 1500,
        "success_rate": 85.5,
        "average_latency": 250,
        "total_vulnerabilities": 12
    }

@app.get("/api/test-runs")
async def get_test_runs():
    """Get test runs."""
    return [
        {
            "run_id": "test-001",
            "model_name": "gpt-3.5-turbo", 
            "status": "completed",
            "created_at": "2024-08-09T20:30:00Z",
            "total_tests": 100,
            "success_rate": 88.0,
            "average_latency": 245
        },
        {
            "run_id": "test-002",
            "model_name": "gpt-4",
            "status": "running", 
            "created_at": "2024-08-09T21:15:00Z",
            "total_tests": 150,
            "success_rate": 92.5,
            "average_latency": 380
        }
    ]

if __name__ == "__main__":
    print("🚀 Starting FailProof LLM Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8080")
    print("🔍 API endpoints:")
    print("   - Health: http://localhost:8080/api/health")
    print("   - Stats: http://localhost:8080/api/stats") 
    print("   - Test Runs: http://localhost:8080/api/test-runs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
