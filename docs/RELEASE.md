# Release Process

This project uses automated semantic versioning based on [Conventional Commits](https://www.conventionalcommits.org/).

## How It Works

1. **Commit Messages Drive Versioning**:

   - `feat:` commits → minor version bump (0.3.0 → 0.4.0)
   - `fix:` or `perf:` commits → patch version bump (0.3.0 → 0.3.1)
   - `BREAKING CHANGE:` or `feat!:` → major version bump (0.3.0 → 1.0.0)
   - Other types (`docs:`, `chore:`, etc.) → no version bump

2. **Automated Release Process**:
   - Manually trigger the "Release" workflow in GitHub Actions
   - Python Semantic Release analyzes commits since last release
   - Generates new version number automatically
   - Updates `pyproject.toml` and `src/openapi_mcp/__init__.py`
   - Creates git tag and GitHub release with changelog
   - Triggers deployment pipeline

## Creating a Release

### Manual Trigger (Recommended)

1. Go to **Actions** → **Release** workflow
2. Click **Run workflow**
3. Select options:
   - **prerelease**: Check for alpha/beta releases
   - **force**: Force release even if no releasable commits
4. Click **Run workflow**

The workflow will:

- ✅ Analyze commits and determine version
- ✅ Create git tag (e.g., `v0.4.0`)
- ✅ Generate CHANGELOG.md
- ✅ Create GitHub release
- ✅ Trigger deployment (Docker + PyPI)

### Version Tag Push (Alternative)

Pushing a version tag directly will also trigger deployment:

```bash
git tag v0.4.0
git push origin v0.4.0
```

## Commit Message Examples

### New Features (Minor Bump)

```bash
git commit -m "feat(tools): add semantic search for API endpoints"
git commit -m "feat(resources): expose security schemes as resource"
```

Result: `0.3.0` → `0.4.0`

### Bug Fixes (Patch Bump)

```bash
git commit -m "fix(server): handle missing docs_url gracefully"
git commit -m "fix(vector-search): correct embedding dimension mismatch"
```

Result: `0.3.0` → `0.3.1`

### Breaking Changes (Major Bump)

```bash
git commit -m "feat!: redesign resource URI structure

BREAKING CHANGE: Resource URIs changed from openapi://spec to openapi://api-specification.
Update your MCP client configurations accordingly."
```

Result: `0.3.0` → `1.0.0`

### Non-Release Commits

```bash
git commit -m "docs: update installation instructions"
git commit -m "chore: update dependencies"
git commit -m "ci: improve workflow caching"
git commit -m "test: add integration tests for tools"
```

Result: No version change

## Version Management

Version is automatically managed in:

- `pyproject.toml` → `project.version`
- `src/openapi_mcp/__init__.py` → `__version__`

**Never manually edit these version numbers** - let semantic-release handle it.

## Deployment Flow

```
Release Workflow
  ↓
Semantic Release analyzes commits
  ↓
Creates version tag (e.g., v0.4.0)
  ↓
Triggers CI/CD Workflow
  ↓
├── Lint & Test
├── Build Python Package
├── Build Docker Image
├── Security Scan
└── Publish to PyPI & ECR
```

## Checking What Will Be Released

To see what version will be created without actually releasing:

```bash
pip install python-semantic-release
semantic-release version --print
```

This shows the next version number based on commits since the last release.

## Release Notes

Release notes are automatically generated from commit messages. The changelog includes:

- **Features**: All `feat:` commits
- **Bug Fixes**: All `fix:` commits
- **Performance**: All `perf:` commits
- **Breaking Changes**: Any commits with `BREAKING CHANGE:`

## Troubleshooting

### No Release Created

If the workflow says "No release created":

- Check that you have commits since the last release
- Ensure commits follow conventional commit format
- Use `force: true` option to override (creates patch bump)

### Version Conflict

If there's a version conflict:

- Pull latest changes: `git pull --tags`
- The workflow uses the latest tag as baseline

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Python Semantic Release](https://python-semantic-release.readthedocs.io/)
- [GitHub Actions Workflows](.github/workflows/)
