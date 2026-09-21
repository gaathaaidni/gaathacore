export class MetricsService {
  private counters = new Map<string, number>();
  increment(name: string, value = 1): void { this.counters.set(name, (this.counters.get(name) ?? 0) + value); }
  set(name: string, value: number): void { this.counters.set(name, value); }
  snapshot(): Record<string, number> { return Object.fromEntries(this.counters.entries()); }
  prometheus(): string { return [...this.counters.entries()].map(([k, v]) => `sentira_${k} ${v}`).join('\n') + '\n'; }
}
