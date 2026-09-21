# File Security

**Status:** PARTIALLY IMPLEMENTED / NOT YET VERIFIED.

The application has an upload folder, CSV import/export task code, signed download tokens, path checks, and a 10 MB Nginx client limit. Complete allowed-type validation, size enforcement at application level, malware scanning, filename policy, retention, storage isolation, and route-wide authorization are not evidenced.

Review every upload, attachment, generated file, export, and download. Verify authenticated access, organization ownership, canonical paths, traversal resistance, and non-public storage before production use.
