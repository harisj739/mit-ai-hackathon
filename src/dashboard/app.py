"""
FastAPI dashboard for Stressor.
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from ..core.storage import StorageManager
from ..core.config import settings

app = FastAPI(title="FailProof LLM Dashboard", version="1.0.0")

# Initialize storage manager
storage_manager = StorageManager()

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = Path(__file__).parent / "templates"
if templates_dir.exists():
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None


class TestRunResponse(BaseModel):
    run_id: str
    model_name: str
    status: str
    created_at: str
    total_tests: int
    success_count: int
    error_count: int
    success_rate: float
    average_latency: float


class TestResultResponse(BaseModel):
    test_id: str
    status: str
    input_data: str
    output_data: Optional[str]
    error_message: Optional[str]
    latency: int
    created_at: str


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FailProof LLM Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: #f5f5f5; padding: 20px; border-radius: 8px; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                .metric { display: inline-block; margin: 10px; padding: 15px; background: #e7f3ff; border-radius: 5px; }
                .metric h3 { margin: 0; color: #0066cc; }
                .metric p { margin: 5px 0; font-size: 24px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>FailProof LLM Dashboard</h1>
                    <p>Stress-testing Framework for AI Systems</p>
                </div>
                <div class="section">
                    <h2>Quick Actions</h2>
                    <a href="/api/test-runs">View Test Runs</a> |
                    <a href="/api/stats">View Statistics</a> |
                    <a href="/api/health">Health Check</a>
                </div>
            </div>
        </body>
        </html>
        """


@app.get("/test-runs", response_class=HTMLResponse)
async def test_runs_page(request: Request):
    """Test runs list page."""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        return dashboard_home(request)


@app.get("/test-runs/{run_id}", response_class=HTMLResponse)
async def test_run_detail_page(request: Request, run_id: str):
    """Test run detail page."""
    if templates:
        return templates.TemplateResponse("test_detail.html", {"request": request, "run_id": run_id})
    else:
        return f"<h1>Test Run: {run_id}</h1><p>Template not available</p>"


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }


@app.get("/api/stats")
async def get_stats():
    """Get overall statistics from real database."""
    try:
        # Get real statistics from the database
        stats = storage_manager.get_storage_stats()
        
        # Calculate real metrics
        total_runs = len(storage_manager.get_recent_runs(limit=1000)) if hasattr(storage_manager, 'get_recent_runs') else 0
        
        return {
            "total_test_runs": total_runs,
            "total_test_cases": stats.get('total_test_cases', 0),
            "success_rate": 0.0,  # Will be calculated from real data
            "average_latency": 0,  # Will be calculated from real data
            "total_vulnerabilities": 0,  # Will be calculated from real data
            "last_run": None  # Will be from real data
        }
    except Exception as e:
        # Return zeros if database error - NO fake data
        return {
            "total_test_runs": 0,
            "total_test_cases": 0,
            "success_rate": 0.0,
            "average_latency": 0,
            "total_vulnerabilities": 0,
            "last_run": None
        }


@app.get("/api/test-runs", response_model=List[TestRunResponse])
async def get_test_runs(limit: int = Query(10, ge=1, le=100)):
    """Get list of test runs from real database."""
    try:
        # Get real test runs from database
        if hasattr(storage_manager, 'get_recent_runs'):
            runs = storage_manager.get_recent_runs(limit=limit)
            return runs
        else:
            # Return empty list if method doesn't exist - NO fake data
            return []
    except Exception as e:
        # Return empty list on error - NO fake data
        return []


@app.get("/api/test-runs/{run_id}", response_model=Dict[str, Any])
async def get_test_run(run_id: str):
    """Get specific test run details."""
    try:
        test_run = storage_manager.get_test_run(run_id)
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        return test_run
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-runs/{run_id}/results", response_model=List[TestResultResponse])
async def get_test_results(run_id: str, limit: int = Query(50, ge=1, le=1000)):
    """Get test results for a specific run."""
    try:
        results = storage_manager.get_test_results(run_id)
        if not results:
            raise HTTPException(status_code=404, detail="Test results not found")
        return results[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{run_id}")
async def get_analysis(run_id: str):
    """Get analysis for a specific test run."""
    try:
        test_run = storage_manager.get_test_run(run_id)
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        results = storage_manager.get_test_results(run_id)
        
        # Perform analysis
        analysis = perform_analysis(results)
        
        return {
            "run_id": run_id,
            "analysis": analysis,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def perform_analysis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform analysis on test results."""
    if not results:
        return {
            "total_tests": 0,
            "success_count": 0,
            "error_count": 0,
            "success_rate": 0.0,
            "failure_categories": {},
            "vulnerabilities": [],
            "average_latency": 0
        }
    
    total_tests = len(results)
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = total_tests - success_count
    
    # Analyze failure categories
    failure_categories = {}
    for result in results:
        if result['status'] != 'success':
            category = result.get('category', 'unknown')
            failure_categories[category] = failure_categories.get(category, 0) + 1
    
    # Detect vulnerabilities
    vulnerabilities = []
    for result in results:
        if result['status'] == 'error' and 'injection' in result.get('error_message', '').lower():
            vulnerabilities.append({
                'type': 'prompt_injection',
                'description': 'Potential prompt injection vulnerability detected',
                'test_case_id': result.get('test_case_id', 'unknown')
            })
    
    return {
        'total_tests': total_tests,
        'success_count': success_count,
        'error_count': error_count,
        'success_rate': (success_count / total_tests * 100) if total_tests > 0 else 0,
        'failure_categories': failure_categories,
        'vulnerabilities': vulnerabilities,
        'average_latency': sum(r.get('latency', 0) for r in results) / total_tests if total_tests > 0 else 0
    }


@app.get("/api/test-runs/{run_id}/export")
async def export_test_results(run_id: str):
    """Export test results as CSV."""
    try:
        # This would export results to CSV
        # For now, return a simple response
        return {
            "message": f"Export for run {run_id} would be generated here",
            "format": "csv",
            "run_id": run_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 