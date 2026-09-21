import { SetMetadata } from '@nestjs/common';
export const REQUIRE_PERMISSION = 'sentira:permission';
export const RequirePermission = (permission: string) => SetMetadata(REQUIRE_PERMISSION, permission);
