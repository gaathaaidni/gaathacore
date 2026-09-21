# Docker Build Troubleshooting

## Vite `Could not resolve "./CustomFieldsPage" from "src/main.jsx"`

This error means the Docker build is compiling a Vite/React frontend that imports
`./CustomFieldsPage` from `src/main.jsx`, but the matching component file is not
present at build time.

Check these items in the repository where the error occurs:

1. Confirm the failing repository path. The current Gaatha AI frontend in this
   repository is a Next.js application under `frontend/app`, not a Vite app under
   `frontend/src`.
2. If the intended project is Vite, restore or create the missing file with the
   exact case expected by the import, for example `frontend/src/CustomFieldsPage.jsx`.
   Linux Docker builds are case-sensitive, so `customFieldsPage.jsx` or
   `CustomfieldsPage.jsx` will not satisfy `./CustomFieldsPage`.
3. If the Vite project no longer uses that page, remove or correct the import in
   `frontend/src/main.jsx` before rebuilding.
4. Rebuild from the repository that contains the failing `Dockerfile` and
   `frontend/src/main.jsx`:

   ```bash
   docker compose down && docker compose up --build
   ```

For this repository, use the Next.js frontend build check instead:

```bash
cd frontend && npm run build
```
