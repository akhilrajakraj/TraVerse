# Chapter 02 — Troubleshooting

## Purpose

This document records every significant issue encountered during the implementation of Chapter 02.

Rather than simply documenting error messages, each issue is analysed to identify its root cause, resolution, preventative measures, and engineering lessons.

The goal is to ensure that future contributors can quickly diagnose similar issues without repeating the same debugging process.

---

# Issue 01 — Django Could Not Create Applications

## Symptoms

Running:

```bash
python manage.py startapp core apps/core
```

resulted in:

```text
CommandError:
Destination directory '/app/apps/core' does not exist,
please create it first.
```

---

## Root Cause

When a destination path is supplied to Django's `startapp` command, Django assumes that the destination directory already exists.

Unlike many file generation tools, `startapp` does not automatically create nested directories.

---

## Resolution

The scaffold script was updated to create each application directory before executing `startapp`.

Example:

```python
app_dir.mkdir(parents=True, exist_ok=True)
```

---

## Prevention

Future automation scripts should always verify directory existence before invoking Django management commands.

---

## Engineering Lesson

Never assume framework commands create required directory structures.

Automation should prepare the environment before invoking external tools.

---

# Issue 02 — Incorrect Project Root Detection

## Symptoms

The scaffold script terminated with:

```text
manage.py not found
```

even though `manage.py` clearly existed.

---

## Root Cause

The script assumed the repository structure remained identical inside the Docker container.

It attempted to locate:

```text
/app/backend/manage.py
```

However, the Docker volume mounted only the backend directory, making the runtime structure:

```text
/app/manage.py
```

---

## Resolution

The project root was recalculated relative to the running script.

Correct implementation:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
```

---

## Prevention

Always write automation against the runtime filesystem, not the repository layout.

---

## Engineering Lesson

Container filesystem layouts may differ significantly from repository layouts.

Automation should always target the runtime environment.

---

# Issue 03 — AppConfig Import Failure

## Symptoms

Running:

```bash
python manage.py check
```

produced:

```text
Cannot import 'core'

Check that apps.core.apps.CoreConfig.name is correct.
```

---

## Root Cause

Every generated AppConfig still contained:

```python
name = "core"
```

while Django expected:

```python
name = "apps.core"
```

because every application resides inside the `apps` package.

---

## Resolution

Every AppConfig was updated.

Example:

```python
class CoreConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.core"

    verbose_name = "Core"
```

---

## Prevention

Projects using nested application packages should always configure fully qualified AppConfig paths.

---

## Engineering Lesson

Django imports applications using the value specified in `AppConfig.name`.

An incorrect value prevents Django from loading the application.

---

# Issue 04 — Automation Failed Silently

## Symptoms

The automation script reported success.

However, inspecting the generated files showed:

```python
name = 'core'
```

had not changed.

---

## Root Cause

The automation script only searched for:

```python
name = "core"
```

using double quotes.

Django generated:

```python
name = 'core'
```

using single quotes.

The regular expression therefore matched nothing.

---

## Resolution

The replacement logic was updated to support both single-quoted and double-quoted values.

Example:

```python
r'name\s*=\s*[\'"][^\'"]+[\'"]'
```

---

## Prevention

Automation should account for multiple valid formatting styles.

---

## Engineering Lesson

Source code formatting is not guaranteed.

Automation should operate on syntax rather than stylistic conventions.

---

# Issue 05 — Incorrect Application Registration

## Symptoms

Applications were added to `INSTALLED_APPS`.

Django still failed during startup.

---

## Root Cause

Application registration occurred before AppConfig values were corrected.

Django therefore attempted to import invalid module paths.

---

## Resolution

The implementation order was changed.

Correct sequence:

1. Create applications
2. Update AppConfig
3. Register applications
4. Validate configuration

---

## Prevention

Always complete application configuration before modifying Django settings.

---

## Engineering Lesson

Order of execution matters.

Correct sequencing reduces cascading configuration errors.

---

# Issue 06 — Missing Runtime Validation

## Symptoms

Configuration changes accumulated before verification.

Errors became more difficult to isolate.

---

## Root Cause

Validation was initially deferred until multiple modifications had already been applied.

---

## Resolution

Validation became mandatory after every significant engineering task.

Standard validation command:

```bash
python manage.py check
```

---

## Prevention

Introduce validation checkpoints throughout implementation.

---

## Engineering Lesson

Small, frequent validation dramatically reduces debugging effort.

---

# Final Validation

The chapter concluded with:

```bash
python manage.py check
```

Result:

```text
System check identified no issues (0 silenced).
```

This confirms:

- All applications are importable.
- Every AppConfig is valid.
- Django settings are correctly configured.
- Application registration is complete.
- The project architecture is healthy.

---

# Summary

The issues encountered during Chapter 02 primarily involved project structure, container path resolution, application configuration, and automation reliability.

Resolving these issues produced a more robust engineering workflow and established reusable automation that will benefit future chapters and contributors.