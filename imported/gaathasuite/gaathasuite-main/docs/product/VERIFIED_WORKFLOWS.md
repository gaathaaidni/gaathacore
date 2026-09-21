# Verified Workflows

## Summary

This document records which workflows are currently backed by evidence in the repository.

## Verified in this environment

- backend bootstrap smoke test
- frontend production build
- Docker Compose config validation
- static compile and diff hygiene validation
- auth and tenant admin smoke paths
- legal acceptance smoke path
- export token scoping smoke path

## Not yet fully verified

- full tenant-isolation negative tests
- full accounting posting and balance validation
- sales order / fulfillment / invoice workflow
- procurement / AP workflow
- expense approval and accounting workflow
- file import/export security tests
- backup and restore rehearsal
- worker / Redis operational test

## Release conclusion

The project is not yet green for a production release.
