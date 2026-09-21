# ADR 0003: Compose Production Topology

- **Status:** Accepted configuration
- **Context:** `docker-compose.prod.yml` defines web, PostgreSQL, Redis, and persistent volumes.
- **Decision:** Keep database and Redis internal to the Compose network; expose the web service locally for Nginx proxying.
- **Alternatives:** Public database/Redis ports; unmanaged host processes.
- **Consequences:** Nginx, volumes, secrets, health checks, and restore procedures remain operator responsibilities.
