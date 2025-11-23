# CHANGELOG

<!-- version list -->

## v1.0.1 (2025-11-23)

### Bug Fixes

- Update mcp version for 2025-06-18 protocol support and otel bootstrap when running in agentcore
  ([`67e32c0`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/67e32c05b56cf55c17df3e8897a2972c6f60eabe))

- **ci**: Update permissions for build docker job and upgrade upload-sarif action version
  ([`b66d6c6`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/b66d6c69c7e7af24eaa2b3c8a3fc76cb50010e37))

### Chores

- Update observability configuration to use ENABLE_TELEMETRY instead of AGENT_OBSERVABILITY_ENABLED
  ([`cdfe43e`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/cdfe43e9ff88564e13e488974fc5d54a432e644c))

- **ci**: Improve docker build caching layers for faster container builds
  ([`ed3eaf0`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/ed3eaf045d9f4a0574ee6edd50ef7269b126099f))

- **ci**: Update Dockerfile and CI to streamline package build and add entrypoint script
  ([`e679a6c`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/e679a6c5267930a9c1c894b2be0c9796551430cb))

- **dev**: Add development environment with hot reloading and OpenTelemetry support
  ([`409fd5a`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/409fd5a3a4c02241f2348221697f645034f65b1d))

- **dev**: Update docker compose setup to test streamable http
  ([`fce8480`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/fce84807fa0bb8c6ed6d0530d8f3fcfcdaf44be0))

- **lint**: Cleaned lint issues
  ([`e83dad2`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/e83dad2cb09335aca432fe764aed02147fd8536d))


## v1.0.0 (2025-11-22)

### Chores

- **ci**: Reorganize CI workflow for improved dependency caching and linting setup
  ([`a0f1ceb`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/a0f1ceb9806db017ebe1ef283f1fd63aaf66b4b8))

- **ci**: Streamline release workflow by removing unnecessary inputs and enhancing artifact handling
  ([`216f7df`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/216f7df65b92d232a731879a2cc79825546ebbb7))

- **ci**: Update job dependencies and improve Docker image handling in CI/CD workflows
  ([`baf2300`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/baf2300f386affa0c40bd85f6ddd38a4c6c4d6fd))

- **lint**: Remove unused imports in test files for cleaner code
  ([`c9792bd`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/c9792bdcf8373b070fdac13794ff179979df16ea))

- **lint**: Update IndexLoader to IndexLoaderProtocol for better type safety
  ([`037fc3c`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/037fc3c89831154d3a7cbded969e2b2000c1eb57))

- **security**: Update supported versions and clarify vulnerability reporting process
  ([`0eb3b9b`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/0eb3b9b54469e380c4b6508786c845ef9dbcca6a))

### Features

- Enhance release workflow with build, deploy, and security scanning steps
  ([`7d32102`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/7d32102ab6bb4968abd031e32a92fd036f1a078d))

- Use correct transport configuration for AgentCore compatibility
  ([`24a5f28`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/24a5f28fd65bf1b8883829183bfca9511543d9b4))

- **ci**: Add GitHub Actions CI/CD workflow and setup documentation
  ([`590d063`](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/commit/590d063eb08fca7ca24c324188012669caf1e530))


## v0.3.0 (2025-11-22)

- Initial Release
