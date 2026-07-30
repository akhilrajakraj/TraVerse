# ADR-009: Use Gunicorn as the Production Application Server

**Status:** Accepted

**Date:** Phase 07

**Decision Type:** Infrastructure

---

# Context

Django provides a built-in development server (`runserver`) that is extremely useful during local development.

The development server offers features such as:

- Automatic code reloading
- Immediate feedback after source code changes
- Simple local execution
- Minimal configuration

However, Django's documentation explicitly states that the development server is **not intended for production use**.

As DockForge evolved into a reusable production-oriented backend infrastructure, a dedicated WSGI application server became necessary.

---

# Problem Statement

The development server prioritizes developer convenience rather than production performance or reliability.

Using it in production introduces several limitations:

- Not optimized for handling concurrent requests
- Limited process management
- Reduced stability under sustained load
- Not intended for internet-facing deployments

DockForge required an application server that was designed specifically for production environments while preserving the rapid development experience locally.

---

# Decision

DockForge adopts two different application servers depending on the deployment environment.

## Development

The development environment uses:

```
python manage.py runserver
```

This provides:

- Automatic code reload
- Fast development cycle
- Simple debugging
- Minimal setup

---

## Production

The production environment uses:

```
Gunicorn
```

Gunicorn becomes the primary WSGI application server responsible for executing the Django application behind Nginx.

---

# Architecture

```
Development

Browser
    │
    ▼
Django Development Server
(runserver)

-----------------------------------

Production

Browser
    │
    ▼
Nginx
    │
    ▼
Gunicorn
    │
    ▼
Django Application
```

The production architecture introduces Gunicorn as an intermediary between Nginx and Django, providing a more robust request handling model.

---

# Alternatives Considered

## Option 1 — Use Django Development Server Everywhere

Advantages:

- Very simple configuration
- No additional dependencies

Disadvantages:

- Not recommended for production
- Limited reliability
- Poor scalability
- Reduced fault tolerance

Result:

Rejected.

---

## Option 2 — Use Gunicorn Everywhere

Advantages:

- Consistent runtime across environments

Disadvantages:

- Slower development workflow
- No automatic code reloading
- Less convenient for local development

Result:

Rejected.

---

## Option 3 — Separate Development and Production Servers

Advantages:

- Optimized developer experience
- Production-oriented deployment
- Clear separation of responsibilities
- Widely adopted industry practice

Disadvantages:

- Two runtime configurations must be maintained

Result:

Accepted.

---

# Consequences

Positive outcomes include:

- Faster local development
- Production-ready request handling
- Improved deployment reliability
- Better scalability
- Clear environment separation

Trade-offs include:

- Different startup commands for each environment
- Additional production dependency

These trade-offs are minimal compared to the operational benefits.

---

# Impact

This decision affects:

- Docker Compose configuration
- Docker images
- Deployment workflow
- Runtime configuration
- Documentation

It also aligns DockForge with common Django deployment practices used in production systems.

---

# Future Considerations

As DockForge continues to evolve, the Gunicorn configuration may be enhanced with additional production tuning.

Potential improvements include:

- Worker process tuning
- Request timeout configuration
- Graceful worker recycling
- Performance optimization
- Metrics collection

These enhancements can be introduced without changing the overall architecture established in Phase 07.

---

# Summary

DockForge separates development and production runtime environments by using Django's built-in development server for local development and Gunicorn for production deployments.

This decision provides an efficient development workflow while ensuring that production environments use an application server designed for reliability, scalability, and long-term maintainability.