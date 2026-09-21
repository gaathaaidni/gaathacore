export const FREE_PLAN = 'FREE';
export const FREE_CAMERA_LIMIT = 3;
export const CAMERA_LIMIT_REACHED = 'CAMERA_LIMIT_REACHED';
export function cameraLimitMessage(plan: string, limit: number): string {
	return `Your ${plan} plan supports up to ${limit} cameras. Please contact us to add more cameras.`;
}
export const CAMERA_LIMIT_MESSAGE = cameraLimitMessage(FREE_PLAN, FREE_CAMERA_LIMIT);