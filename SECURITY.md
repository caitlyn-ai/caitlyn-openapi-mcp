# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3.0 | :x:                |

## Reporting a Vulnerability

We take the security of caitlyn-openapi-mcp seriously. If you believe you have found a security vulnerability, please report it to us responsibly.

### Please Do Not

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### How to Report

**Email:** security@caitlyn.ai

Please include the following information in your report:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** of the vulnerability
4. **Suggested fix** (if you have one)
5. **Your contact information** for follow-up questions

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report as soon as possible
2. **Assessment**: We will investigate and assess the severity of the vulnerability
3. **Updates**: We will keep you informed about our progress
4. **Resolution**: We will work to fix confirmed vulnerabilities and release a patch
5. **Credit**: With your permission, we will credit you in the security advisory and release notes

### Disclosure Timeline

We aim to address security vulnerabilities promptly, though response times may vary as this is an open-source project maintained by volunteers. We request that you:

- Allow reasonable time for us to investigate and patch the vulnerability before public disclosure
- Coordinate with us on the disclosure timeline
- Avoid publicizing the vulnerability until a fix is available

For critical vulnerabilities, we will prioritize a rapid response.

## Security Best Practices

When using caitlyn-openapi-mcp, we recommend:

1. **Environment Variables**: Never commit `.env` files or expose sensitive environment variables
2. **OpenAPI Spec URLs**: Ensure your `OPENAPI_SPEC_URL` points to a trusted source
3. **Network Security**: When deploying with `streamable-http` transport, use proper network security (firewalls, VPCs, etc.)
4. **Authentication**: If deploying to production, implement proper authentication and authorization
5. **HTTPS Only**: Always use HTTPS for `OPENAPI_SPEC_URL` and `DOCS_BASE_URL` in production
6. **Regular Updates**: Keep the package and its dependencies up to date

## Known Security Considerations

### OpenAPI Spec Loading

This server loads OpenAPI specifications from URLs specified in environment variables. Ensure:

- The URL is from a trusted source
- The URL uses HTTPS
- You have reviewed the OpenAPI spec for any sensitive information

### MCP Transport Modes

- **stdio**: Runs as a subprocess, inherits permissions from the parent process
- **streamable-http**: Exposes an HTTP endpoint - ensure proper network security

## Security Updates

Security updates will be published as:

- GitHub Security Advisories
- New releases on PyPI
- Notifications in the project README

Subscribe to this repository to receive notifications about security updates.

## Bug Bounty Program

We do not currently offer a bug bounty program, but we deeply appreciate responsible disclosure and will acknowledge your contribution publicly (with your permission).

## Contact

For security-related questions or concerns:

- **Email**: security@caitlyn.ai
- **General Issues**: For non-security bugs, please use [GitHub Issues](https://github.com/caitlyn-ai/caitlyn-openapi-mcp/issues)

Thank you for helping keep caitlyn-openapi-mcp and our users safe!
