# Stressor Documentation

## Overview

Stressor is a comprehensive stress-testing framework designed to help enterprises and developers proactively test and harden their AI systems before production deployment. By systematically testing with diverse adversarial inputs, we can discover weaknesses early and improve reliability.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Security Considerations](#security-considerations)
6. [Storage Considerations](#storage-considerations)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd failproof-llm
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

```bash
cp env.example .env
# Edit .env with your API keys and configurations
```

### Step 4: Initialize Database

```bash
python -c "from src.core.storage import StorageManager; StorageManager()"
```

## Quick Start

### 1. Generate Test Cases

Generate adversarial test cases:

```bash
python -m src.cli generate --count 20 --type adversarial --output data/test_cases.json
```

Generate prompt injection test cases:

```bash
python -m src.cli generate --count 10 --type prompt_injection --output data/injection_tests.json
```

### 2. Run Stress Tests

Run tests against an OpenAI model:

```bash
python -m src.cli run --model gpt-3.5-turbo --test-cases data/test_cases.json --output results.json
```

### 3. View Results

Start the dashboard:

```bash
python -m src.cli dashboard --port 8080
```

Then visit `http://localhost:8080` in your browser.
```

### Configuration Files

Create custom configurations in YAML format:

```yaml
# configs/custom_test.yaml
generation:
  adversarial:
    count: 100
    categories:
      - malformed_json
      - special_characters

execution:
  model: gpt-4
  max_concurrent: 10
  timeout: 60
```

## Usage

### Command Line Interface

#### Generate Test Cases

```bash
# Generate adversarial test cases
python -m src.cli generate --count 50 --type adversarial

# Generate specific category
python -m src.cli generate --count 20 --type adversarial --category malformed_json

# Save to file
python -m src.cli generate --count 30 --type prompt_injection --output my_tests.json
```

#### Run Tests

```bash
# Run with default test cases
python -m src.cli run --model gpt-3.5-turbo

# Run with custom test cases
python -m src.cli run --model gpt-4 --test-cases my_tests.json

# Run with concurrent execution
python -m src.cli run --model gpt-3.5-turbo --concurrent 10
```

#### Analyze Results

```bash
# Analyze specific run
python -m src.cli analyze --run-id run_20240101_120000_gpt-3.5-turbo

# Analyze all runs
python -m src.cli analyze

# Export analysis
python -m src.cli analyze --run-id run_id --output analysis.json
```

### Programmatic Usage

#### Basic Usage

```python
from src.generators import AdversarialGenerator
from src.runners import OpenAIRunner
from src.core.storage import StorageManager

# Generate test cases
generator = AdversarialGenerator()
test_cases = generator.generate(count=50)

# Run tests
runner = OpenAIRunner(model_name="gpt-3.5-turbo")
results = await runner.run_concurrent_tests(test_cases, max_concurrent=5)

# Save results
storage = StorageManager()
run_id = storage.save_results(results)
```

#### Advanced Usage

```python
import asyncio
from src.generators import PromptInjectionGenerator
from src.runners import OpenAIRunner

async def run_comprehensive_test():
    # Generate various test types
    adversarial_gen = AdversarialGenerator()
    injection_gen = PromptInjectionGenerator()
    
    test_cases = []
    test_cases.extend(adversarial_gen.generate(30))
    test_cases.extend(injection_gen.generate(20))
    
    # Run tests
    runner = OpenAIRunner(model_name="gpt-4")
    results = await runner.run_concurrent_tests(test_cases, max_concurrent=3)
    
    # Analyze results
    analysis = perform_analysis(results)
    return analysis

# Run the test
results = asyncio.run(run_comprehensive_test())
```

## Security Considerations

### API Key Management

1. **Secure Storage**: API keys are encrypted at rest using Fernet encryption
2. **Environment Variables**: Store keys in environment variables, not in code
3. **Rotation**: Implement key rotation policies for production use
4. **Monitoring**: Monitor API usage and detect anomalies

### Input Sanitization

1. **Validation**: All inputs are validated before processing
2. **Sanitization**: Potentially malicious inputs are sanitized
3. **Logging**: Security events are logged for audit purposes

### Rate Limiting

1. **Per-minute Limits**: Configurable requests per minute
2. **Per-hour Limits**: Configurable requests per hour
3. **Backoff Strategy**: Exponential backoff for rate limit errors

### Data Privacy

1. **Local Processing**: Sensitive data can be processed locally
2. **Encryption**: Data is encrypted in transit and at rest
3. **Retention**: Configurable data retention policies

## Storage Considerations

### Database Options

1. **SQLite**: Default for development and testing
2. **PostgreSQL**: Recommended for production
3. **MongoDB**: Alternative for document storage

### Data Organization

```
failproof-llm/
├── data/                    # Test data and results
│   ├── test_cases/         # Generated test cases
│   ├── results/            # Test results
│   └── analysis/           # Analysis reports
├── backups/                # Database backups
├── logs/                   # Application logs
└── configs/                # Configuration files
```

### Backup Strategy

1. **Automated Backups**: Daily automated backups
2. **Versioning**: Test case and result versioning
3. **Retention**: Configurable retention periods
4. **Recovery**: Automated recovery procedures

## API Reference

### Core Classes

#### AdversarialGenerator

Generates adversarial test cases for stress testing.

```python
class AdversarialGenerator(BaseGenerator):
    def generate(self, count: int = 1, **kwargs) -> List[Dict[str, Any]]
    def generate_specific_adversarial(self, category: str, **kwargs) -> Dict[str, Any]
```

#### PromptInjectionGenerator

Generates prompt injection test cases for security testing.

```python
class PromptInjectionGenerator(BaseGenerator):
    def generate(self, count: int = 1, **kwargs) -> List[Dict[str, Any]]
    def generate_specific_injection(self, injection_type: str, **kwargs) -> Dict[str, Any]
```

#### OpenAIRunner

Runs tests against OpenAI models.

```python
class OpenAIRunner(BaseRunner):
    async def run_single_test(self, test_case: Dict[str, Any], **kwargs) -> Dict[str, Any]
    async def run_concurrent_tests(self, test_cases: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]
```

#### StorageManager

Manages data storage and persistence.

```python
class StorageManager:
    def save_test_run(self, run_data: Dict[str, Any]) -> str
    def save_test_result(self, result_data: Dict[str, Any]) -> int
    def get_test_run(self, run_id: str) -> Optional[Dict[str, Any]]
    def get_test_results(self, run_id: str) -> List[Dict[str, Any]]
```

## Troubleshooting

### Common Issues

#### API Key Errors

**Problem**: `ValueError: OpenAI API key must be provided`

**Solution**: 
1. Set `OPENAI_API_KEY` in your `.env` file
2. Ensure the key is valid and has proper permissions

#### Rate Limiting

**Problem**: Rate limit exceeded errors

**Solution**:
1. Increase delays between requests
2. Reduce concurrent request count
3. Implement exponential backoff

#### Database Errors

**Problem**: Database connection failures

**Solution**:
1. Check database URL in configuration
2. Ensure database service is running
3. Verify permissions and connectivity

#### Memory Issues

**Problem**: High memory usage with large test sets

**Solution**:
1. Reduce batch sizes
2. Implement streaming for large datasets
3. Use database pagination

### Getting Help

1. **Documentation**: Check this documentation first
2. **Issues**: Search existing GitHub issues
3. **Discussions**: Use GitHub Discussions for questions
4. **Support**: Contact the development team

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 