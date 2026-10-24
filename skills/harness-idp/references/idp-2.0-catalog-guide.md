# Harness IDP 2.0 Catalog & Entity Modeling Guide

## Overview

Harness IDP 2.0 adopts the Backstage v1alpha1 catalog entity model, extended with Harness native RBAC, project scopes, and pipeline integrations.

## Core Entity Kinds

### 1. `Component`
Represents an individual software unit (service, website, library).
```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: auth-service
  description: OAuth2 and session authentication service
  tags:
    - python
    - auth
  annotations:
    backstage.io/techdocs-ref: dir:.
    github.com/project-slug: my-org/auth-service
    harness.io/project-url: https://app.harness.io/ng/account/ACC/home/orgs/ORG/projects/PROJ
spec:
  type: service
  lifecycle: production
  owner: identity-team
  system: platform-core
  providesApis:
    - auth-api
```

### 2. `API`
Surfaces API definitions (OpenAPI, gRPC, GraphQL, AsyncAPI) within the catalog.
```yaml
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: auth-api
  description: Authentication and Token Issuance API
spec:
  type: openapi
  lifecycle: production
  owner: identity-team
  system: platform-core
  definition:
    $text: ./openapi.yaml
```

### 3. `Template` (Software Scaffolder)
Defines self-service scaffolding workflows for developers.
```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: create-microservice
  title: Microservice Starter Template
  description: Scaffolds a new cloud-ready microservice with CI/CD
spec:
  owner: platform-team
  type: service
  parameters:
    - title: Service Configuration
      required:
        - service_name
      properties:
        service_name:
          title: Service Name
          type: string
  steps:
    - id: fetch-template
      name: Fetch Skeleton
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.service_name }}
    - id: publish-github
      name: Publish Repository
      action: publish:github
      input:
        repoUrl: github.com?repo=${{ parameters.service_name }}&owner=my-org
```
