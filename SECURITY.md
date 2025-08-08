# Security Policy

## Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in Entity, please follow these steps:

### 1. Do Not Open a Public Issue

**Please do not report security vulnerabilities through public GitHub issues.** Public disclosure of security vulnerabilities puts the entire community at risk.

### 2. Report Privately

Instead, please send your report privately to:

- **Email**: cthomasbrittain@hotmail.com
- **Subject Line**: [SECURITY] Entity Framework Vulnerability Report

### 3. Include Detailed Information

Please include as much information as possible in your report:

- A clear description of the vulnerability
- Steps to reproduce the vulnerability
- Potential impact of the vulnerability
- Any suggested fixes or mitigations you may have
- Your contact information for follow-up questions

### 4. Our Response Process

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.

2. **Investigation**: We will investigate and validate the reported vulnerability within 5 business days.

3. **Coordination**: If the vulnerability is confirmed, we will work with you to:
   - Understand the full scope of the issue
   - Develop and test a fix
   - Plan the disclosure timeline
   - Coordinate the release of security patches

4. **Resolution**: We aim to release security fixes within 30 days of confirmation, depending on the complexity of the fix.

5. **Public Disclosure**: After the fix is released, we will publish a security advisory with:
   - Description of the vulnerability
   - Affected versions
   - Fixed versions
   - Credit to the reporter (if desired)

## Security Best Practices

When using Entity in production:

### Agent Security
- **Input Validation**: Always validate and sanitize user inputs before passing them to agents
- **LLM Prompt Injection**: Be aware of prompt injection attacks and implement appropriate filtering
- **Resource Isolation**: Use proper user isolation (`user_id` parameter) for multi-tenant applications

### Infrastructure Security
- **Secrets Management**: Never commit API keys, tokens, or sensitive configuration to version control
- **Network Security**: Secure your LLM infrastructure endpoints (vLLM, Ollama) with proper authentication
- **Database Security**: Secure your DuckDB files and S3 buckets with appropriate access controls

### Dependency Security
- **Regular Updates**: Keep Entity and its dependencies updated
- **Vulnerability Scanning**: Use tools like `pip-audit` or `safety` to scan for known vulnerabilities
- **Dependabot**: Enable Dependabot for automated security updates

### Configuration Security
- **Environment Variables**: Use environment variables for sensitive configuration
- **File Permissions**: Secure configuration files and logs with appropriate permissions
- **Logging**: Avoid logging sensitive information like API keys or user data

## Security Features

Entity includes several built-in security features:

### Resource Isolation
- **User Separation**: Each `user_id` gets isolated memory and context
- **Plugin Sandboxing**: Plugins operate within controlled resource boundaries
- **Database Isolation**: User data is separated at the database level

### Input Safety
- **Type Validation**: All resources use Pydantic for input validation
- **SQL Injection Protection**: Database queries use parameterized statements
- **File System Isolation**: File storage is sandboxed to designated directories

### Monitoring
- **Audit Logging**: All user actions and system events are logged
- **Health Checks**: Built-in health monitoring for all infrastructure components
- **Error Handling**: Secure error messages that don't leak sensitive information

## Known Security Considerations

### AI/LLM Specific Risks
1. **Prompt Injection**: External input could manipulate LLM behavior
2. **Data Leakage**: LLMs might leak training data or previous conversation context
3. **Hallucination**: LLMs may generate false information that appears authoritative

### Mitigation Strategies
- Implement input filtering and validation
- Use separate LLM instances for different security contexts
- Monitor and log all LLM interactions
- Validate LLM outputs before taking actions

## Updates to This Policy

This security policy may be updated from time to time. Updates will be published in this file and announced in release notes.

## Contact

For general security questions or concerns, please contact:
- Email: cthomasbrittain@hotmail.com
- GitHub: @Ladvien

Thank you for helping keep Entity and its users safe!
