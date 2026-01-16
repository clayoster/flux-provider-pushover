# flux-provider-pushover

This is a middleware service that can be used to send alerts from FluxCD into Pushover. 

FluxCD has no native notification providers ([documentation](https://fluxcd.io/flux/components/notification/providers/)), and the `generic` provider does not support sending authentication to Pushover in the way that is necessary. This service handles authentication in a way that works with the `generic` provider and will pivot notifications into Pushover using your user key and application API token.

Container images are based on Alpine Linux and are available for these platforms:
  - linux/amd64
  - linux/arm64

---

## How to send FluxCD Alerts to this Application

Add Provider and Alert configurations like the ones below to your flux repository.

```yaml
# clusters/cluster-name/alerts.yaml

apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: pushover
  namespace: flux-system
spec:
  type: generic
  # The secretRef holds the address and header with the Authorization token
  secretRef:
    name: pushover-credentials
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: flux-alerts
  namespace: flux-system
spec:
  providerRef:
    name: pushover
  # Available options for eventSeverity: info, error
  eventSeverity: error
  eventSources:
    - kind: 'Bucket'
      name: '*'
    - kind: GitRepository
      name: '*'
    - kind: HelmChart
      name: '*'
    - kind: HelmRelease
      name: '*'
    - kind: HelmRepository
      name: '*'
    - kind: ImageRepository
      name: '*'
    - kind: ImagePolicy
      name: '*'
    - kind: ImageUpdateAutomation
      name: '*'
    - kind: Kustomization
      name: '*'
    - kind: OCIRepository
      name: '*'
```

Add a secret that provides configuration to the pushover provider. Your Pushover application API token is used as the bearer token to authenticate to the service
```yaml
apiVersion: v1
kind: Secret
metadata:
    name: pushover-credentials
    namespace: flux-system
stringData:
    # Address for flux-provider-pushover
    address: https://flux-provider-pushover.example.com/webhook
    # Send an Authorization header that includes the
    # Pushover Application API Token
    headers: |
        Authorization: Bearer your_pushover_application_token
```

## Deployment Options

The application must be presented with the `PUSHOVER_USER_KEY` and `PUSHOVER_API_TOKEN` environment variables containing the appropriate values for your Pushover configuration. If these are not presented, the application will exit immediately.

### Kubernetes (Recommended)

Example Kubernetes manifest file defining the following items:
- Namespace
- Secret
- Deployment (A single pod with health checks)
- Service
- Ingress (Configured for nginx ingress with example domain "flux-provider-pushover.example.com")

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: flux-provider-pushover
---
apiVersion: v1
kind: Secret
metadata:
  name: flux-provider-pushover
  namespace: flux-provider-pushover
type: Opaque
stringData:
    PUSHOVER_USER_KEY: your_pushover_user_key
    PUSHOVER_API_TOKEN: your_pushover_application_token
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flux-provider-pushover
  namespace: flux-provider-pushover
  labels:
    app: flux-provider-pushover
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flux-provider-pushover
  template:
    metadata:
      labels:
        app: flux-provider-pushover
    spec:
      containers:
        - name: flux-provider-pushover
          image: ghcr.io/clayoster/flux-provider-pushover:latest
          env:
            - name: PUSHOVER_USER_KEY
              valueFrom:
                secretKeyRef:
                  name: flux-provider-pushover
                  key: PUSHOVER_USER_KEY
            - name: PUSHOVER_API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: flux-provider-pushover
                  key: PUSHOVER_API_TOKEN
          ports:
            - containerPort: 8080
              name: 8080tcp
              protocol: TCP
          resources: {}
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
              scheme: HTTP
            initialDelaySeconds: 10
            periodSeconds: 30
            successThreshold: 1
            timeoutSeconds: 3
            failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: flux-provider-pushover
  namespace: flux-provider-pushover
spec:
  selector:
    app: flux-provider-pushover
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-provider-pushover
  namespace: flux-provider-pushover
spec:
  ingressClassName: nginx
  rules:
    - host: flux-provider-pushover.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: flux-provider-pushover
                port:
                  number: 80
```

Additional recommendations:
- Only run this container on an internal network and not exposed to the internet
- Run this behind ingress with HTTPS configured to keep requests encrypted
