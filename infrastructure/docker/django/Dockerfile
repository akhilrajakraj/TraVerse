# ==========================
# Builder Stage
# ==========================
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv

WORKDIR /app

# Create virtual environment
RUN python -m venv $VIRTUAL_ENV

# Use the virtual environment
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first (better Docker cache)
COPY backend/requirements/base.txt /tmp/base.txt

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/base.txt

# ==========================
# Runtime Stage
# ==========================
FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Create a non-root group and user
RUN groupadd --system django && \
    useradd --system --gid django --create-home django

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Install curl for Docker health checks
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy application source
COPY backend/ /app/

# Set ownership
RUN chown -R django:django /app /opt/venv

# Switch to the non-root user
USER django

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]