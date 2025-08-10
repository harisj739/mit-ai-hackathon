#!/usr/bin/env python3
"""
Basic example demonstrating Stressor usage.

This example shows how to:
1. Generate adversarial test cases
2. Run stress tests against an OpenAI model
3. Analyze and display results
"""

import asyncio
import json
from pathlib import Path

from src.generators import AdversarialGenerator, PromptInjectionGenerator
from src.runners import OpenAIRunner
from src.core.storage import StorageManager
from src.core.config import settings


async def main():
    """Main example function."""
    print("Stressor - Basic Example")
    print("=" * 50)
    
    # Initialize components
    print("\n1. Initializing components...")
    storage_manager = StorageManager()
    adversarial_generator = AdversarialGenerator()
    injection_generator = PromptInjectionGenerator()
    
    # Generate test cases
    print("\n2. Generating test cases...")
    adversarial_cases = adversarial_generator.generate(5)
    injection_cases = injection_generator.generate(3)
    
    all_test_cases = adversarial_cases + injection_cases
    print(f"   Generated {len(all_test_cases)} test cases:")
    print(f"   - {len(adversarial_cases)} adversarial cases")
    print(f"   - {len(injection_cases)} prompt injection cases")
    
    # Save test cases
    test_cases_file = Path("data") / "example_test_cases.json"
    test_cases_file.parent.mkdir(exist_ok=True)
    
    with open(test_cases_file, 'w') as f:
        json.dump(all_test_cases, f, indent=2)
    print(f"   Test cases saved to: {test_cases_file}")
    
    # Check if OpenAI API key is available
    if not settings.openai_api_key:
        print("\n OpenAI API key not found in environment variables.")
        print("   Please set OPENAI_API_KEY in your .env file or environment.")
        print("   Skipping test execution...")
        
        # Display some test cases instead
        print("\n3. Sample test cases:")
        for i, test_case in enumerate(all_test_cases[:3], 1):
            print(f"\n   Test Case {i}:")
            print(f"   - Name: {test_case['name']}")
            print(f"   - Category: {test_case['category']}")
            print(f"   - Description: {test_case['description']}")
            print(f"   - Input: {test_case['input_data'][:100]}...")
        
        return
    
    # Initialize runner
    print("\n3. Initializing OpenAI runner...")
    runner = OpenAIRunner(model_name="gpt-5")
    
    # Run tests
    print("\n4. Running stress tests...")
    print("   This may take a few minutes...")
    
    results = await runner.run_concurrent_tests(all_test_cases, max_concurrent=2)
    
    # Save results
    results_file = Path("data") / "example_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"   Results saved to: {results_file}")
    
    # Display summary
    print("\n5. Test Results Summary:")
    stats = runner.get_stats()
    print(f"   - Total Tests: {stats['total_tests']}")
    print(f"   - Success Rate: {stats['success_rate']:.1f}%")
    print(f"   - Average Latency: {stats['average_latency']:.0f}ms")
    print(f"   - Errors: {stats['error_count']}")
    
    # Analyze results
    print("\n6. Analysis:")
    analysis = perform_analysis(results)
    
    if analysis['vulnerabilities']:
        print(f"   - Vulnerabilities Found: {len(analysis['vulnerabilities'])}")
        for vuln in analysis['vulnerabilities']:
            print(f"     * {vuln['type']}: {vuln['description']}")
    else:
        print("   - No vulnerabilities detected")
    
    if analysis['failure_categories']:
        print("   - Failure Categories:")
        for category, count in analysis['failure_categories'].items():
            print(f"     * {category}: {count}")
    
    print("\nExample completed successfully!")
    print("\nNext steps:")
    print("1. Review the generated test cases in data/example_test_cases.json")
    print("2. Check the test results in data/example_results.json")
    print("3. Start the dashboard: python -m src.cli dashboard")
    print("4. Run more comprehensive tests with custom configurations")


def perform_analysis(results):
    """Perform basic analysis on test results."""
    total_tests = len(results)
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = total_tests - success_count
    
    # Analyze failure categories
    failure_categories = {}
    for result in results:
        if result['status'] != 'success':
            category = result['status']  # Use the actual status as the category
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
    asyncio.run(main()) 