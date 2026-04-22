# -----------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Install system dependencies needed to compile some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy and install Python dependencies into a virtual environment
COPY requirements/prod.txt requirements/prod.txt
COPY requirements/base.txt requirements/base.txt

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir -r requirements/prod.txt

# -----------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------
FROM python:3.11-slim

LABEL maintainer="home-decor@example.com"
LABEL description="Home Decor e-commerce backend"

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /venv /venv

# Set the working directory
WORKDIR /app

# Copy the application source
COPY --chown=appuser:appgroup . .

# Make the entrypoint executable
RUN chmod +x entrypoint.sh && \
    mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appgroup /app/staticfiles /app/media

# Activate the virtual environment by adding it to PATH
ENV PATH="/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

# Switch to the non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/products/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
