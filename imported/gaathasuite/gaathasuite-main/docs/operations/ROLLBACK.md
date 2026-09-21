# Rollback

**Status:** PLANNED / deployment-specific.

Before release, record the image/tag, migration, backup, and rollback owner. If application code fails, restore the prior image and verify health. If a migration changed schema, do not blindly downgrade; restore a tested backup or apply a reviewed forward fix. Run login and critical workflow smoke tests after rollback.
