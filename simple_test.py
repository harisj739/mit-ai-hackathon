#!/usr/bin/env python3
"""
Super simple dashboard test
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

# Create FastAPI app
app = FastAPI(title="FailProof LLM Dashboard")

# Setup static files
dashboard_dir = Path("src/dashboard")
if dashboard_dir.exists() and (dashboard_dir / "static").exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_dir / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Main dashboard page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FailProof LLM Dashboard</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.min.js"></script>
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="/static/css/dashboard.css">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="bi bi-shield-check"></i>
                FailProof LLM
            </a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/">
                            <i class="bi bi-house"></i> Dashboard
                        </a>
                    </li>
                </ul>
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <span class="navbar-text">
                            <i class="bi bi-clock"></i>
                            <span id="last-updated">Loading...</span>
                        </span>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container-fluid py-4">
        <!-- Page Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h1 class="h2 mb-1">
                            <i class="bi bi-shield-check text-primary"></i>
                            FailProof LLM Dashboard
                        </h1>
                        <p class="text-muted mb-0">Stress-testing Framework for AI Systems</p>
                    </div>
                    <div>
                        <button class="btn btn-primary" onclick="refreshData()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Stats Cards -->
        <div class="row mb-4">
            <div class="col-xl-3 col-md-6 mb-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="stat-icon bg-primary">
                                <i class="bi bi-list-check"></i>
                            </div>
                            <div class="ms-3">
                                <div class="text-muted small">Total Test Runs</div>
                                <div class="h4 mb-0" id="stat-total-runs">--</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-xl-3 col-md-6 mb-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="stat-icon bg-success">
                                <i class="bi bi-check-circle"></i>
                            </div>
                            <div class="ms-3">
                                <div class="text-muted small">Success Rate</div>
                                <div class="h4 mb-0" id="stat-success-rate">--%</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-xl-3 col-md-6 mb-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="stat-icon bg-warning">
                                <i class="bi bi-exclamation-triangle"></i>
                            </div>
                            <div class="ms-3">
                                <div class="text-muted small">Vulnerabilities</div>
                                <div class="h4 mb-0" id="stat-vulnerabilities">--</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-xl-3 col-md-6 mb-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="stat-icon bg-info">
                                <i class="bi bi-clock"></i>
                            </div>
                            <div class="ms-3">
                                <div class="text-muted small">Avg Response</div>
                                <div class="h4 mb-0" id="stat-avg-latency">-- ms</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row mb-4">
            <div class="col-lg-8 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-graph-up"></i>
                            Success Rate Trend
                        </h5>
                    </div>
                    <div class="card-body">
                        <canvas id="success-trend-chart" height="100"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-pie-chart"></i>
                            Failure Categories
                        </h5>
                    </div>
                    <div class="card-body">
                        <canvas id="failure-categories-chart" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Test Runs -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-clock-history"></i>
                            Recent Test Runs
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover" id="test-runs-table">
                                <thead>
                                    <tr>
                                        <th>Run ID</th>
                                        <th>Model</th>
                                        <th>Status</th>
                                        <th>Created</th>
                                        <th>Tests</th>
                                        <th>Success Rate</th>
                                        <th>Avg Latency</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="test-runs-tbody">
                                    <tr>
                                        <td colspan="8" class="text-center text-muted">
                                            <div class="py-4">
                                                <i class="bi bi-hourglass-split fs-1"></i>
                                                <div>Loading test runs...</div>
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Loading Spinner Overlay -->
    <div id="loading-overlay" class="loading-overlay d-none">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Custom JS -->
    <script src="/static/js/dashboard.js"></script>
    
    <script>
    // Initialize dashboard when page loads
    document.addEventListener('DOMContentLoaded', function() {
        initializeDashboard();
        
        // Set up auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Set up search and filter functionality
        setupSearchAndFilter();
    });
    </script>
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
    print("🔍 Open your web browser and go to: http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
