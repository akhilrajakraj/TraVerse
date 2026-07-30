# PostgreSQL Integration Architecture

## Document Information

| Field | Value |
|-------|-------|
| Phase | Phase 4 |
| Module | PostgreSQL Integration |
| Project | DockForge |
| Status | Completed |
| Last Updated | July 2026 |

---

# Objective

The objective of this phase was to replace Django's default SQLite database with PostgreSQL running inside a Docker container.

This migration prepares DockForge for enterprise-level backend development by introducing a production-ready relational database system.

---

# Why PostgreSQL?

SQLite is an excellent database for learning and small applications.

However, enterprise systems require features such as:

- Multiple concurrent users
- Better transaction handling
- High reliability
- Index optimization
- Better scalability
- Production deployment support

PostgreSQL satisfies these requirements and is one of the most widely used relational databases in modern backend development.

---

# Architecture Overview

                  Windows Host
                        │
                        │
                Django Application
                (manage.py / Runserver)
                        │
                 psycopg Database Driver
                        │
                localhost:5432
                        │
                 Docker Engine
                        │
        PostgreSQL 17 Docker Container
                        │
            Persistent Docker Volume

---

# Components

## Django

Responsible for:

- ORM
- Database Migrations
- Authentication
- Admin Panel

---

## psycopg

The PostgreSQL driver used by Django.

Responsibilities

- Open database connections
- Execute SQL
- Transfer query results
- Handle transactions

---

## PostgreSQL 17

Database server running inside Docker.

Responsibilities

- Store persistent application data
- Execute SQL queries
- Maintain transactions
- Manage users and permissions

---

## Docker Volume

Volume Name

compose_postgres_data

Purpose

Ensures that database data survives even if the PostgreSQL container is removed.

---

# Environment Variables

The following environment variables were introduced.

POSTGRES_DB

Database name

POSTGRES_USER

Database administrator username

POSTGRES_PASSWORD

Database password

POSTGRES_HOST

Database hostname

POSTGRES_PORT

Database listening port

---

# Django Connection Flow

User Request

↓

Django ORM

↓

psycopg

↓

localhost:5432

↓

Docker PostgreSQL

↓

Persistent Volume

---

# Outcome

At the end of Phase 4,

DockForge successfully communicates with PostgreSQL instead of SQLite.

All future database operations, migrations, authentication, and application models will use PostgreSQL.