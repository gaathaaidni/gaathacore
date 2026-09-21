# CCTV Catalog

The API catalog is seeded from `apps/api/src/database/seeds/cctv/catalog.ts`. It contains stable manufacturer slugs, representative product families, protocol metadata, discovery method hints, and user-facing setup guides. Catalog entries describe guided onboarding only; they do not claim live compatibility or replace connector integrations.

## Seed and update

The existing `seedDatabase(dataSource)` entry point calls `seedCctvCatalog`. Run the normal database seed command used by the deployment, or invoke that exported function from an authenticated TypeORM seed runner after migrations have completed. The catalog seed does not drop or reset data.

Catalog writes are deterministic:

- Manufacturers are matched by `slug`.
- Models are matched by `manufacturerId` and `slug`.
- Guides are matched by manufacturer, model, and title.

Add a manufacturer to `CCTV_MANUFACTURERS`, a product family to `CCTV_MODELS`, and a guide to `CCTV_GUIDES`. Use a stable slug and keep protocol status `verified: false` unless the exact device and firmware have been tested. Never add passwords, tokens, or private connection details to catalog data.

## Support boundaries

ONVIF discovery, RTSP streaming, and recorder channel discovery are runtime connector behavior. A catalog entry and a guide are not live-device verification. Keep `DISCOVERY_UNAVAILABLE` and other real connector outcomes unchanged. Hardware verification should be reported separately for the exact model, firmware, network path, and connector.

Guides intentionally warn users to use private LAN/VPN access, dedicated least-privilege accounts, secure transport where available, credential rotation, and no credentials in frontend code or logs. Recording on a camera, NVR/DVR, NAS, or vendor cloud is distinct from Sentira evidence storage; unsupported proprietary storage integrations must not be implied by a catalog entry.
