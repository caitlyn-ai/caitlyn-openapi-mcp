# Contributing to Caitlyn OpenAPI MCP

Thank you for your interest in contributing to Caitlyn OpenAPI MCP! This document provides guidelines and instructions for contributing.

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) to automatically generate version numbers and changelogs. Please follow this format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature (triggers minor version bump, e.g., 0.3.0 → 0.4.0)
- **fix**: A bug fix (triggers patch version bump, e.g., 0.3.0 → 0.3.1)
- **perf**: Performance improvement (triggers patch version bump)
- **docs**: Documentation only changes (no version bump)
- **style**: Code style changes (formatting, missing semicolons, etc., no version bump)
- **refactor**: Code refactoring (no version bump)
- **test**: Adding or updating tests (no version bump)
- **chore**: Maintenance tasks (no version bump)
- **ci**: CI/CD changes (no version bump)
- **build**: Build system changes (no version bump)

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the commit body or add `!` after the type:

```
feat!: remove deprecated API endpoint

BREAKING CHANGE: The /v1/old-endpoint has been removed. Use /v2/new-endpoint instead.
```

This triggers a major version bump (e.g., 0.3.0 → 1.0.0).

### Examples

```bash
# New feature (minor bump)
git commit -m "feat(tools): add semantic search for endpoints"

# Bug fix (patch bump)
git commit -m "fix(server): handle missing docs_url gracefully"

# Performance improvement (patch bump)
git commit -m "perf(vector-search): optimize embedding cache"

# Documentation (no bump)
git commit -m "docs: update installation instructions"

# Breaking change (major bump)
git commit -m "feat!: redesign resource URIs

BREAKING CHANGE: Resource URIs changed from openapi://spec to openapi://api-specification"
```

## Releasing

Releases are automated using Python Semantic Release:

1. **Automatic Release**: When ready, manually trigger the "Release" workflow in GitHub Actions

   - It analyzes commits since the last release
   - Generates a new version number based on commit types
   - Creates a git tag and GitHub release
   - Generates a changelog
   - Triggers the deployment pipeline

2. **Manual Version Control**: The version is managed automatically in:
   - `pyproject.toml`
   - `src/openapi_mcp/__init__.py`

## Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/caitlyn-ai/caitlyn-openapi-mcp.git
cd caitlyn-openapi-mcp
```

2. **Install dependencies**

```bash
make install-dev
# or
pip install -e ".[dev]"
```

3. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your OpenAPI spec URL and docs base URL
```

## Development Workflow

### Interactive Testing

The recommended development workflow uses MCP Inspector with telemetry:

```bash
# Start dev environment (OTEL + Jaeger + Inspector)
make dev

# Test the server interactively in the web UI
# View telemetry at http://localhost:16686

# Stop when done
make dev-stop
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_config.py

# Run tests matching a pattern
pytest -k test_load_config
```

### Testing Telemetry

```bash
# Test OTEL integration
make otel-up
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 python scripts/test_telemetry.py

# View results in Jaeger
open http://localhost:16686
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code with Black
make format

# Run linting with Ruff
make lint

# Type checking with Pyright
make type-check

# Run all checks
make format && make lint && make type-check && make test
```

### Running the Server Locally

**For development with MCP Inspector and telemetry (recommended):**

```bash
# Start everything: OTEL Collector + Jaeger + MCP Inspector
make dev

# View telemetry in Jaeger UI
open http://localhost:16686

# Stop everything
make dev-stop
```

**For direct execution:**

```bash
# Set required environment variables
export OPENAPI_SPEC_URL="https://api.example.com/openapi.json"
export DOCS_BASE_URL="https://api.example.com/docs"

# Run the server
python -m openapi_mcp.server
```

**OTEL Collector commands:**

```bash
# Start OTEL collector standalone
make otel-up

# View collector logs
make otel-logs

# Stop collector
make otel-down
```

See [TELEMETRY.md](docs/TELEMETRY.md) for complete telemetry documentation.

### Docker Development

```bash
# Build Docker image
make docker-build

# Run with docker-compose
make docker-run

# View logs
make docker-logs

# Stop
make docker-stop
```

## Code Style

- **Line length**: 160 characters (configured in pyproject.toml)
- **Python version**: 3.11+
- **Type hints**: Use type hints for all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Formatting**: Use Black for code formatting
- **Linting**: Use Ruff for linting

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Use pytest fixtures for common test data
- Mark slow tests with `@pytest.mark.slow`
- Mark integration tests with `@pytest.mark.integration`

## Pull Request Process

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**

```bash
# Test interactively with MCP Inspector
make dev

# Run unit tests
make test-cov
```

4. **Run quality checks**

```bash
make format
make lint
make type-check
```

5. **Commit your changes**

```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

6. **Push and create a pull request**

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Checklist

- [ ] Code follows the project style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, docstrings)
- [ ] Commit messages follow conventional commits
- [ ] No merge conflicts with main branch

## Adding New Features

### Adding a New Documentation Renderer

To add support for a new documentation renderer (e.g., Redoc, Swagger UI):

1. **Update [docs_links.py](src/openapi_mcp/docs_links.py)**

   - Add a new function `_attach_<renderer>_links()`
   - Update `attach_docs_links()` to handle the new renderer

2. **Add tests in [test_docs_links.py](tests/test_docs_links.py)**

3. **Update documentation**
   - Update README.md with the new renderer option
   - Add example configuration

### Adding New MCP Resources

1. **Update [resources.py](src/openapi_mcp/resources.py)**

   - Add new resource decorator in `register_resources()`

2. **Add tests in [test_resources.py](tests/test_resources.py)**

3. **Update README.md** with the new resource documentation

### Adding New MCP Tools

1. **Update [tools.py](src/openapi_mcp/tools.py)**

   - Add new tool decorator in `register_tools()`

2. **Add tests** as appropriate

3. **Update README.md** with the new tool documentation

## Security Vulnerabilities

**Do not open public issues for security vulnerabilities.**

If you discover a security vulnerability, please follow our [Security Policy](SECURITY.md) for responsible disclosure. We appreciate your efforts to responsibly disclose your findings and will make every effort to acknowledge your contributions.

- **Email**: security@caitlyn.ai
- **See**: [SECURITY.md](SECURITY.md) for full details

## Release Process

Releases are published to PyPI and follow semantic versioning:

1. Version bump in `pyproject.toml`
2. Update CHANGELOG.md with release notes
3. Create a Git tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions builds and publishes to PyPI
6. Create GitHub Release with release notes

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Getting Help

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Security**: Use security@caitlyn.ai for security vulnerabilities

## Community Guidelines

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to adhere to these guidelines:

### Our Standards

**Positive behaviors include:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members
- Providing and gracefully receiving constructive feedback
- Acknowledging and learning from mistakes

**Unacceptable behaviors include:**

- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting
- Spam or self-promotion without value to the community

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at security@caitlyn.ai. All complaints will be reviewed and investigated promptly and fairly.

Project maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, issues, and other contributions that do not align with these guidelines.

### Attribution

These community guidelines are adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.1.

## Recognition

We value and recognize all contributions to this project:

- **Code contributors** are listed in the project's Git history
- **Issue reporters** help improve the project quality
- **Documentation contributors** make the project more accessible
- **Community members** who help others in discussions

Significant contributions may be highlighted in release notes and project documentation.

## License

By contributing to caitlyn-openapi-mcp, you agree that your contributions will be licensed under the [MIT License](LICENSE).

You also certify that:

1. Your contribution is your original work or you have the right to submit it
2. You grant Caitlyn Team and recipients of this software a perpetual, worldwide, non-exclusive, royalty-free license to use your contribution

## Questions?

If you have any questions about contributing, please:

- Open a [GitHub Discussion](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/discussions)
- Review existing [Issues](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/issues)
- Check the [README](README.md) for project documentation

Thank you for contributing to caitlyn-openapi-mcp! 🎉
