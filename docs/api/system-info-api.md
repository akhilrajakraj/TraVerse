# System Information API

**Phase:** 07 – Infrastructure Monitoring & Production Readiness

---

# Overview

The System Information API provides runtime information about the DockForge backend environment.

Unlike the Health API, which determines whether the application is operational, this endpoint exposes useful system information that helps developers verify application configuration during development and deployment.

The endpoint is primarily intended for:

- Environment verification
- Infrastructure validation
- Deployment testing
- Development debugging
- Configuration inspection

---

# Endpoint

```
GET /system-info/
```

---

# Purpose

The endpoint provides information about the currently running application instance.

Typical use cases include:

- Confirming the application is responding correctly
- Verifying runtime configuration
- Inspecting deployment information
- Supporting development and testing workflows

Unlike the Health API, this endpoint is informational rather than diagnostic.

---

# Request

## HTTP Method

```
GET
```

## Authentication

None

## Request Body

None

---

# Successful Response

A successful request returns information describing the running application.

**Status Code**

```
200 OK
```

The exact response depends on the current implementation.

---

# Response Structure

The response contains runtime information exposed by the application.

Depending on the implementation, this may include information such as:

- Application name
- Environment
- Runtime information
- Version details
- Infrastructure metadata

Only information intentionally exposed by the application should be considered part of the public API.

---

# Example Response

The following illustrates the general structure of a successful response.

```json
{
    "application": "DockForge",
    "environment": "development",
    "status": "running"
}
```

> **Note**
>
> The actual fields returned by the endpoint depend on the current implementation and may evolve over time.

---

# Typical Use Cases

The System Information API is useful for:

- Confirming the correct environment is running
- Verifying deployment configuration
- Checking application availability
- Assisting during infrastructure setup
- Supporting local development

---

# Relationship with the Health API

Although both endpoints are related to infrastructure, they serve different purposes.

| Endpoint | Purpose |
|----------|---------|
| `/health/` | Verifies operational health of application dependencies |
| `/system-info/` | Provides information about the running application |

The Health API determines whether the backend is operational.

The System Information API describes the environment in which the backend is running.

---

# Implementation Notes

The endpoint is intentionally lightweight.

It does not perform dependency verification or health checks.

Instead, it returns information that helps developers understand the current application instance without modifying server state.

Because the endpoint is read-only, repeated requests do not affect application behavior.

---

# Security Considerations

Care should be taken when exposing runtime information.

Only non-sensitive information should be returned.

Examples of information that **should not** be exposed include:

- Secret keys
- Database passwords
- API credentials
- Authentication tokens
- Internal security configuration

Keeping sensitive configuration private reduces the risk of accidental information disclosure.

---

# Future Enhancements

Future versions of this endpoint may include additional metadata, such as:

- Application version
- Build information
- Python version
- Django version
- Container identifier
- Deployment timestamp
- Host information
- Uptime

These enhancements are planned for future phases and are not part of the current implementation.

---

# Summary

The System Information API provides a simple, read-only interface for inspecting the current DockForge application instance.

By exposing selected runtime information, the endpoint assists with development, deployment verification, and infrastructure validation while remaining separate from the health monitoring system.