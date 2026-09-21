import { classifyDependencyHealth } from './health.service';

describe('classifyDependencyHealth', () => {
  it.each([
    [{ probeConfigured: false }, 'UNKNOWN'],
    [{ probeConfigured: true }, 'UNKNOWN'],
    [{ probeConfigured: true, reachable: false }, 'UNAVAILABLE'],
    [{ probeConfigured: true, reachable: true, latencyMs: 1200 }, 'DEGRADED'],
    [{ probeConfigured: true, reachable: true, latencyMs: 10 }, 'HEALTHY'],
  ])('classifies %j as %s', (input, expected) => {
    expect(classifyDependencyHealth(input)).toBe(expected);
  });
});