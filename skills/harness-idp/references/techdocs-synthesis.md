# Harness TechDocs Architecture & Synthesis Guide

## Overview

Harness TechDocs provides "docs-as-code" technical documentation hosted alongside microservices, generated using MkDocs and rendered natively within the Harness IDP service catalog.

## Repository Setup (`mkdocs.yml`)

Place an `mkdocs.yml` file in the root of your microservice or documentation repository:

```yaml
site_name: Service API & Architecture Docs
site_description: Technical documentation for payment service

nav:
  - Overview: index.md
  - Architecture: architecture.md
  - API Reference: api.md

plugins:
  - techdocs-core
```

Documentation markdown files reside in the `docs/` folder:
```text
repo-root/
├── mkdocs.yml
├── docs/
│   ├── index.md
│   ├── architecture.md
│   └── api.md
└── catalog-info.yaml
```

## Catalog Entity Annotation

Link the documentation to your IDP Catalog Component in `catalog-info.yaml`:

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payment-service
  description: Core payment handling microservice
  annotations:
    # Points to directory containing mkdocs.yml relative to repo root
    backstage.io/techdocs-ref: dir:.
spec:
  type: service
  lifecycle: production
  owner: payments-team
```

## TechDocs Build & Storage Architecture

TechDocs supports two generation models:
1. **Harness Cloud Generation (Default)**: Harness automates the MkDocs build container directly in the cloud whenever the source repository is updated.
2. **CI Pipeline Generation (Self-hosted / Custom Storage)**:
   - Build step: Runs `@techdocs/cli` to generate static HTML from markdown.
   - Publish step: Publishes static assets to an S3 bucket or Google Cloud Storage bucket configured in Harness IDP Settings.
