# File Security

**Status:** PARTIALLY IMPLEMENTED / NOT YET VERIFIED.

The source includes upload storage, exports, signed download tokens, and path checks. Nginx limits request bodies to 10 MB. Allowed MIME types/extensions, malware scanning, application-level size limits, retention, and complete tenant authorization are not proven.

Treat file security as a release blocker for sensitive documents until upload/download tests cover authentication, ownership, traversal, generated files, and cross-tenant access.
