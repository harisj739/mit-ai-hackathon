"""
FastAPI dashboard for Stressor.
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from ..core.storage import StorageManager
from ..core.config import settings

app = FastAPI(title="FailProof LLM Dashboard", version="1.0.0")
app.mount("/", StaticFiles(directory="/Users/hj739/hamzacode/mit-ai-hackathon-1/src/dashboard/app/build"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage manager
storage_manager = StorageManager()

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class TestRunResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
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
    """Get overall statistics."""
    try:
        stats = storage_manager.get_overall_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-runs")
async def get_test_runs(limit: int = Query(10, ge=1, le=100)):
    """Get list of test runs."""
    try:
        test_runs = storage_manager.get_all_test_runs(limit)
        # Transform data to match React frontend expectations
        formatted_runs = []
        for run in test_runs:
            # Calculate stats for this run
            run_results = storage_manager.get_test_results(run['run_id'])
            total_cases = len(run_results)
            success_count = sum(1 for r in run_results if r['status'] == 'success')
            success_rate = (success_count / total_cases * 100) if total_cases > 0 else 0
            avg_latency = sum(r.get('latency', 0) for r in run_results) / total_cases if total_cases > 0 else 0
            
            formatted_runs.append({
                'id': run['run_id'],
                'name': run['name'],
                'status': run['status'],
                'created_at': run['created_at'],
                'total_cases': total_cases,
                'success_rate': success_rate,
                'average_latency': avg_latency
            })
        
        return formatted_runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/seed-data")
async def seed_test_data():
    """Seed the database with sample test data for demonstration."""
    try:
        import uuid
        from datetime import datetime, timedelta
        import random
        
        # Create sample test runs
        for i in range(5):
            run_id = str(uuid.uuid4())
            run_data = {
                'run_id': run_id,
                'model_name': f'gpt-{4 + i % 2}',
                'status': 'completed' if i < 4 else 'running',
                'config': {'temperature': 0.7, 'max_tokens': 2048},
                'results': {},
                'metadata': {'test_type': 'adversarial'}
            }
            storage_manager.save_test_run(run_data)
            
            # Create sample test results for each run
            for j in range(random.randint(10, 50)):
                result_data = {
                    'test_run_id': run_id,
                    'test_case_id': f'test_{j}',
                    'status': 'success' if random.random() > 0.2 else 'error',
                    'input_data': f'Test prompt {j}',
                    'output_data': f'Response {j}' if random.random() > 0.2 else None,
                    'error_message': 'Injection detected' if random.random() > 0.8 else None,
                    'latency': random.randint(500, 3000),
                    'metadata': {'category': random.choice(['adversarial', 'prompt_injection', 'edge_case'])}
                }
                storage_manager.save_test_result(result_data)
        
        return {"message": "Sample data seeded successfully", "runs_created": 5}
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 