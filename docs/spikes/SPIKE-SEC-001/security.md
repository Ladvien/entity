# SPIKE-SEC-001: Sandbox and Signing Strategies

## Summary
This spike surveys sandboxing options and code signing approaches for the Entity Pipeline. It records a simple threat model to guide future security work.

## Sandboxing Approaches
### Docker
- Uses Linux namespaces and cgroups for process and network isolation.
- Provides reproducible environments with explicit resource limits.
- Supports dropping capabilities or running in rootless mode.

### chroot
- Restricts a process to a new filesystem root.
- Shares the host kernel, so isolation is weaker than containers.
- Useful for limiting file access when full Docker is unnecessary.

### virtualenv
- Isolates Python dependencies only.
- Does not prevent system calls or file access.
- Helpful for dependency conflicts but not a security boundary.

## Code Signing
- Sign plugin packages with a trusted certificate and verify during load.
- Options include `gpg` signatures or OS‑level signing tools.
- Keep signing keys offline and restrict who can publish signed packages.

## Permission Models
- Grant each plugin the minimum required filesystem and network access.
- Docker allows capabilities and seccomp profiles to limit system calls.
- Maintain a manifest describing allowed resources and enforce it at runtime.

## Threat Model
### Assets to Protect
- Confidential user data and API keys.
- Integrity of plugin code and configuration.

### Potential Adversaries
- Malicious plugin authors or compromised dependencies.
- Attackers exploiting vulnerabilities to gain code execution.
- Insiders misusing privileged access.

### Attack Vectors
- Unsigned or tampered plugin packages.
- Escaping the sandbox to access host resources.
- Exfiltrating secrets via network calls.

### Mitigations
- Verify plugin signatures before loading.
- Run plugins in containers with read‑only mounts and limited networking.
- Enforce role‑based permissions for secrets and file access.
- Monitor audit logs for suspicious activity.
