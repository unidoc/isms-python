# Contributing to isms-python

Thank you for your interest in contributing.

## Process

1. **Open an issue first** to discuss the change you'd like to make.
2. Fork the repository and create a feature branch.
3. Make your changes and ensure tests pass.
4. Submit a pull request referencing the issue.

## Development Setup

- Python 3.10+

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
ruff check src tests
pytest
```

Both run in CI on every pull request across Python 3.10–3.13.

## Code Style

- **Ruff** for linting and formatting (`ruff check src tests`). Line length 100.
- Full type hints; the package ships a `py.typed` marker.
- Keep commits focused. One logical change per commit.
- The client mirrors the ISMS REST API — new resources/endpoints must match the
  server's actual routes.

## License

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](LICENSE).
