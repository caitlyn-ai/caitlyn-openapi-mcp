# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

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

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
2. **Assessment**: We will investigate and assess the vulnerability within 5 business days
3. **Updates**: We will keep you informed about our progress in addressing the vulnerability
4. **Resolution**: We will work to fix confirmed vulnerabilities and release a patch as quickly as possible
5. **Credit**: With your permission, we will credit you in the security advisory and release notes

### Disclosure Timeline

- **Day 0**: You report the vulnerability
- **Day 1-2**: We acknowledge receipt
- **Day 3-7**: We assess and validate the vulnerability
- **Day 8-30**: We develop and test a fix
- **Day 30+**: We release a patch and publish a security advisory

If the vulnerability is exceptionally critical, we will expedite this timeline.

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
