# Contributing to Logits Analyzer

Thank you for your interest in contributing to Logits Analyzer! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (Python version, SGLang version, model used)
- Relevant logs or error messages

### Suggesting Features

Feature requests are welcome! Please create an issue with:
- A clear description of the feature
- Use cases and motivation
- Potential implementation approach (optional)

### Pull Requests

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Run the test suite** to ensure all tests pass
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description

## Development Setup

### Prerequisites

- Python 3.9+
- SGLang with EAGLE support
- A compatible model (GLM-5, Qwen, LLaMA, etc.)

### Installation

```bash
# Clone your fork
git clone https://github.com/your-username/logits-analyzer.git
cd logits-analyzer

# Install in editable mode with all dependencies
pip install -e ".[all]"
```

### Running Tests

```bash
# Unit tests (fast, no server needed)
pytest logits_analyzer/tests/ -v

# Integration tests (requires live SGLang server)
pytest logits_analyzer/tests/ \
    --run-integration \
    --server-url http://localhost:8000 \
    --model /path/to/model \
    --tokenizer /path/to/tokenizer \
    -v

# Generate HTML test report
pytest logits_analyzer/tests/ \
    --run-integration \
    --server-url http://localhost:8000 \
    --model /path/to/model \
    --tokenizer /path/to/tokenizer \
    --html=report.html \
    --self-contained-html \
    -v
```

## Code Style

### Python

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and concise

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests when relevant

Example:
```
Add support for Medusa speculative decoding

- Implement MedusaCollector class
- Add medusa_quality skill for analysis
- Update tests to cover Medusa cycles

Fixes #123
```

### Documentation

- Update README.md for user-facing changes
- Update SKILLS.md for new analysis tools
- Update DESIGN.md for architectural changes
- Add examples for new features

## Testing Guidelines

### Unit Tests

- Test individual functions and classes in isolation
- Use mock data when possible
- Aim for high code coverage
- Keep tests fast (< 1 second each)

### Integration Tests

- Test end-to-end workflows
- Use real SGLang server and models
- Verify data integrity (100% reconstruction)
- Mark with `@pytest.mark.integration`

### Test Structure

```python
def test_feature_name():
    """Brief description of what is being tested."""
    # Arrange
    input_data = ...

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

## Adding New Skills

To add a new analysis skill:

1. Create `logits_analyzer/skills/your_skill.py`
2. Implement the main analysis function
3. Add CLI entry point with argparse
4. Write unit tests in `tests/test_skills.py`
5. Add integration test in `tests/test_integration.py`
6. Document in SKILLS.md

Example structure:

```python
"""
your_skill.py — Brief description

用法:
    python -m logits_analyzer.skills.your_skill \
        --data-dir cycle_data_202603220000 \
        --request-id abc123
"""

import argparse
import sys
from pathlib import Path


def analyze(cycles: list) -> dict:
    """
    Main analysis function.

    Args:
        cycles: List of cycle dictionaries

    Returns:
        Analysis results as dictionary
    """
    # Your analysis logic here
    return {"metric": value}


def main():
    parser = argparse.ArgumentParser(description="Your skill description")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--request-id", required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parents[2]))
    from logits_analyzer.lib.cycle_data import CycleData

    cd = CycleData(args.data_dir)
    cycles = cd.load_cycles(args.request_id)
    result = analyze(cycles)

    # Print results
    print(f"Metric: {result['metric']}")


if __name__ == "__main__":
    main()
```

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with release notes
3. Create a git tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
4. Push tag: `git push origin v0.2.0`
5. Create GitHub release with changelog

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Reach out to maintainers
- Check existing issues and pull requests

Thank you for contributing to Logits Analyzer!
