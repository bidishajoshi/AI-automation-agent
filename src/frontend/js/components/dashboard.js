/**
 * Dashboard Component - Health telemetry, counters, and card updates
 */

import { qs } from '../utils/dom.js';

export class Dashboard {
  constructor() {
    this.healthElem = qs('#systemHealthVal');
    this.commitElem = qs('#dailyCommitVal');
    this.a11yElem = qs('#a11yScoreVal');
    this.latencyElem = qs('#uiLatencyVal');
  }

  updateMetrics(metrics) {
    if (this.healthElem && metrics.health !== undefined) {
      this.healthElem.textContent = `${metrics.health}%`;
    }
    if (this.commitElem && metrics.commits !== undefined) {
      this.commitElem.textContent = `${metrics.commits} / ${metrics.target || 4}`;
    }
    if (this.a11yElem && metrics.a11yScore !== undefined) {
      this.a11yElem.textContent = `${metrics.a11yScore}%`;
    }
    if (this.latencyElem && metrics.latencyMs !== undefined) {
      this.latencyElem.textContent = `${metrics.latencyMs}ms`;
    }
  }
}
