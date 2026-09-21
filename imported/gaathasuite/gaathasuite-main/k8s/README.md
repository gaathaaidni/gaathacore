# Kubernetes manifests for Gaatha Suite

Files:
- `secret.yaml` — Kubernetes Secret for `DATABASE_URL`, `SECRET_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (base64 values).
- `postgres-deployment.yaml` / `postgres-service.yaml` — optional Postgres StatefulSet/Service for local clusters.
- `web-deployment.yaml` / `web-service.yaml` — Deployment and Service for the Gaatha Suite web app.

Notes:
- Production clusters should use a managed Postgres (RDS, Cloud SQL) and not the included Postgres deployment.
- Fill in secrets with secure base64-encoded values before applying.

Apply example (using a managed DB):

kubectl create secret generic gaatha-secrets \
  --from-literal=DATABASE_URL='postgresql+psycopg2://user:pass@host:5432/dbname' \
  --from-literal=SECRET_KEY='replace-with-secure-value'

kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-service.yaml
