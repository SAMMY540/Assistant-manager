# Assistant-manager

Tools and utilities for managing the Sammy Production 2026 Shopify store
([sammy-production-store.myshopify.com](https://sammy-production-store.myshopify.com)).

## Overview

This repository contains automation and monitoring utilities for the store,
starting with a store health monitoring module that checks:

- Product catalog integrity
- Payment gateway configuration
- Store URL validation

## Project structure

```
.
├── src/
│   └── store_health.py      # Store health monitoring utilities
├── tests/
│   └── test_store_health.py # Unit tests
├── ci.yml                   # GitHub Actions CI
├── pyproject.toml           # Project configuration
└── README.md
```

## Getting started

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run the health check directly
python -m src.store_health
```

## Requirements

- Python 3.10+

No runtime dependencies required.