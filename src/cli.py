"""
Command-line interface for Stressor.
"""

import click
import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .core.config import settings
from .core.logger import setup_logging, get_logger
from .core.storage import StorageManager
from .generators import AdversarialGenerator, PromptInjectionGenerator
from .runners import OpenAIRunner, StressRunner

logger = get_logger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
def cli(debug: bool, config: str):
    """FailProof LLM - Stress-testing Framework for AI Systems."""
    global settings # Declare settings as global

    # Set up logging
    log_level = 'DEBUG' if debug else settings.log_level
    setup_logging(log_level=log_level)
    
    # Load custom config if provided
    if config:
        settings = settings.load_from_file(config)
    
    logger.info("FailProof LLM CLI initialized")


@cli.command()
@click.option('--count', default=10, help='Number of test cases to generate')
@click.option('--type', 'test_type', default='adversarial', 
              type=click.Choice(['adversarial', 'prompt_injection', 'edge_case']),
              help='Type of test cases to generate')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--category', help='Specific category to generate')
def generate(count: int, test_type: str, output: str, category: str):
    """Generate test cases for stress testing."""
    
    logger.info(f"Generating {count} {test_type} test cases")
    
    # Initialize generator
    if test_type == 'adversarial':
        generator = AdversarialGenerator()
    elif test_type == 'prompt_injection':
        generator = PromptInjectionGenerator()
    else:
        click.echo(f"Unsupported test type: {test_type}")
        return
    
    # Generate test cases
    if category:
        test_cases = []
        for _ in range(count):
            if test_type == 'adversarial':
                test_case = generator.generate_specific_adversarial(category)
            elif test_type == 'prompt_injection':
                test_case = generator.generate_specific_injection(category)
            test_cases.append(test_case)
    else:
        test_cases = generator.generate(count)
    
    # Save or display results
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(test_cases, f, indent=2)
        
        logger.info(f"Generated {len(test_cases)} test cases saved to {output_path}")
    else:
        # Display summary
        click.echo(f"Generated {len(test_cases)} {test_type} test cases:")
        for i, test_case in enumerate(test_cases[:5], 1):
            click.echo(f"  {i}. {test_case['name']} - {test_case['category']}")
        
        if len(test_cases) > 5:
            click.echo(f"  ... and {len(test_cases) - 5} more")


@cli.command()
@click.option('--model', default='gpt-5', help='Model to test')
@click.option('--test-cases', type=click.Path(exists=True), help='Test cases file path')
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.option('--output', type=click.Path(), help='Results output path')
@click.option('--concurrent', default=5, help='Number of concurrent tests')
async def run(model: str, test_cases: str, config: str, output: str, concurrent: int):
    """Run stress tests against an LLM."""
    
    logger.info(f"Starting stress test for model: {model}")
    
    # Load test cases
    if test_cases:
        test_cases_path = Path(test_cases)
        with open(test_cases_path, 'r') as f:
            test_cases_data = json.load(f)
    else:
        # Generate default test cases
        generator = AdversarialGenerator()
        test_cases_data = generator.generate(20)
    
    # Initialize runner
    runner = OpenAIRunner(model_name=model)
    
    # Run tests
    results = await runner.run_concurrent_tests(test_cases_data, max_concurrent=concurrent)
    
    # Save results
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
    else:
        # Display summary
        stats = runner.get_stats()
        click.echo(f"\nTest Results Summary:")
        click.echo(f"  Total Tests: {stats['total_tests']}")
        click.echo(f"  Success Rate: {stats['success_rate']:.1f}%")
        click.echo(f"  Average Latency: {stats['average_latency']:.0f}ms")
        click.echo(f"  Errors: {stats['error_count']}")


@cli.command()
@click.option('--port', default=8080, help='Dashboard port')
@click.option('--host', default='0.0.0.0', help='Dashboard host')
def dashboard(port: int, host: str):
    """Start the web dashboard."""
    
    logger.info(f"Starting dashboard on {host}:{port}")
    
    try:
        import uvicorn
        from .dashboard.app import app
        
        uvicorn.run(app, host=host, port=port)
    
    except ImportError:
        click.echo("Dashboard dependencies not installed. Install with: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        click.echo(f"Failed to start dashboard: {e}")


@cli.command()
@click.option('--run-id', help='Specific test run ID to analyze')
@click.option('--output', type=click.Path(), help='Analysis output path')
def analyze(run_id: str, output: str):
    """Analyze test results."""
    
    logger.info("Starting analysis")
    
    storage_manager = StorageManager()
    
    if run_id:
        # Analyze specific run
        test_run = storage_manager.get_test_run(run_id)
        if not test_run:
            click.echo(f"Test run not found: {run_id}")
            return
        
        results = storage_manager.get_test_results(run_id)
    else:
        # Analyze all recent runs
        # This would need to be implemented in StorageManager
        click.echo("Analyzing all recent runs...")
        return
    
    # Perform analysis
    analysis = perform_analysis(results)
    
    # Save or display results
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Analysis saved to {output_path}")
    else:
        # Display summary
        click.echo(f"\nAnalysis Results:")
        click.echo(f"  Total Tests: {analysis['total_tests']}")
        click.echo(f"  Success Rate: {analysis['success_rate']:.1f}%")
        click.echo(f"  Failure Categories:")
        for category, count in analysis['failure_categories'].items():
            click.echo(f"    {category}: {count}")
        
        if analysis['vulnerabilities']:
            click.echo(f"  Vulnerabilities Found: {len(analysis['vulnerabilities'])}")
            for vuln in analysis['vulnerabilities'][:3]:
                click.echo(f"    - {vuln['type']}: {vuln['description']}")


def perform_analysis(results: list) -> Dict[str, Any]:
    """Perform analysis on test results."""
    
    total_tests = len(results)
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = total_tests - success_count
    
    # Analyze failure categories
    failure_categories = {}
    for result in results:
        if result['status'] != 'success':
            category = result['metadata'].get('category', 'unknown')
            failure_categories[category] = failure_categories.get(category, 0) + 1
    
    # Detect vulnerabilities
    vulnerabilities = []
    for result in results:
        if result['status'] == 'error' and 'injection' in result.get('error_message', '').lower():
            vulnerabilities.append({
                'type': 'prompt_injection',
                'description': 'Potential prompt injection vulnerability detected',
                'test_case_id': result['test_case_id']
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


@cli.command()
@click.option('--days', default=30, help='Number of days to keep')
def cleanup(days: int):
    """Clean up old test data and backups."""
    
    logger.info(f"Cleaning up data older than {days} days")
    
    storage_manager = StorageManager()
    storage_manager.cleanup_old_backups(days)
    
    click.echo(f"Cleanup completed for data older than {days} days")


@cli.command()
def version():
    """Show version information."""
    from . import __version__
    click.echo(f"FailProof LLM v{__version__}")


if __name__ == '__main__':
    cli() 