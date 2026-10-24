# Harness GitOps Application Specification

Harness GitOps natively integrates Argo CD application manifests with Harness project/org access controls.

## Application Structure

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/my-org/payments-manifests.git
    targetRevision: main
    path: k8s/overlays/prod
    # For Helm sources:
    # helm:
    #   valueFiles:
    #     - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: payments
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
```

## API Management Endpoints
From official `specs/upstream/harness-applications-api.yaml`:
- `GET /gitops/api/v1/agents/{agentIdentifier}/applications`: List all applications on agent.
- `POST /gitops/api/v1/agents/{agentIdentifier}/applications`: Register new GitOps application.
- `GET /gitops/api/v1/agents/{agentIdentifier}/applications/{name}/sync`: Trigger application sync.
