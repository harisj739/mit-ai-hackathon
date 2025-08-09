# Stressor - Stress-testing Framework for AI Systems

A comprehensive stress-testing framework that bombards LLMs and AI agents with edge cases, malformed inputs, and adversarial scenarios to identify vulnerabilities and improve robustness.

## Project Overview

Stressor is designed to help enterprises and developers proactively test and harden their AI systems before production deployment. By systematically testing with diverse adversarial inputs, we can discover weaknesses early and improve reliability.

## Core Features

### 1. Test Case Generator
- **Adversarial Inputs**: Malformed JSON, misspellings, mixed languages
- **Edge Cases**: Contradictory instructions, very long inputs, special characters
- **Prompt Injections**: Various injection techniques and patterns
- **Domain-Specific**: Industry-relevant scenarios (healthcare, legal, financial)

### 2. Automated Stress Runner
- **Multi-Model Support**: OpenAI, Anthropic, Hugging Face, local models
- **Comprehensive Monitoring**: Response tracking, latency, error detection
- **Batch Processing**: Efficient testing across multiple scenarios

### 3. Failure Analysis Dashboard
- **Failure Classification**: Refusal, crash, incorrect output, policy violation
- **Visual Reports**: Interactive dashboards with actionable insights
- **Metrics Tracking**: Robustness scores, vulnerability assessments

## Architecture

```
stressor/
├── src/
│   ├── core/                 # Core framework components
│   ├── generators/           # Test case generators
│   ├── runners/             # Stress testing runners
│   ├── analyzers/           # Failure analysis
│   ├── dashboards/          # Web dashboard
│   └── utils/               # Utilities and helpers
├── tests/                   # Unit and integration tests
├── data/                    # Test datasets and examples
├── config/                  # Configuration files
├── docs/                    # Documentation
└── examples/                # Usage examples
```

## Installation

```bash
# Clone the repository
git clone https://github.com/harisj739/mit-ai-hackathon.git
cd failproof-llm

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configurations
```

## Quick Start

```bash
# Run a basic stress test
python -m stressor.cli run --model openai --config configs/basic_test.yaml

# Generate custom test cases
python -m stressor.cli generate --type adversarial --output data/custom_tests.json

# View dashboard
python -m stressor.dashboard serve --port 8080
```

## Security Considerations

- **API Key Management**: Secure storage and rotation of API keys
- **Rate Limiting**: Respectful API usage with configurable limits
- **Data Privacy**: Local processing options for sensitive data
- **Input Sanitization**: Safe handling of potentially malicious inputs
- **Audit Logging**: Comprehensive logging for compliance

## Storage Considerations

- **Local Storage**: SQLite for metadata, JSON for test data
- **Cloud Options**: PostgreSQL, MongoDB support
- **Data Retention**: Configurable retention policies
- **Backup Strategy**: Automated backups and versioning

## Testing Strategy

- **Unit Tests**: Comprehensive test coverage
- **Integration Tests**: End-to-end testing with real models
- **Performance Tests**: Load testing and benchmarking
- **Security Tests**: Vulnerability assessment

## Evaluation Metrics

- **Coverage**: Variety and richness of test cases
- **Detection Rate**: Ability to identify failures
- **False Positives**: Minimizing incorrect failure reports
- **Performance**: Testing efficiency and speed
- **Usability**: Ease of configuration and deployment

## 🔮 Roadmap

- [ ] Self-improving test generation
- [ ] Domain-specific test suites
- [ ] Real-time monitoring
- [ ] CI/CD integration
- [ ] Enterprise features 