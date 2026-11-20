/**
 * Analytics and Telemetry Component
 */

export class Analytics {
  constructor() {
    this.historyTableBody = document.getElementById('historyTableBody');
  }

  renderHistory(historyEntries) {
    if (!this.historyTableBody) return;
    this.historyTableBody.innerHTML = '';

    if (!historyEntries || historyEntries.length === 0) {
      const row = document.createElement('tr');
      row.innerHTML = `<td colspan="6" style="text-align:center; color: var(--text-muted); padding: 2rem;">No commit history recorded yet.</td>`;
      this.historyTableBody.appendChild(row);
      return;
    }

    historyEntries.forEach(entry => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${entry.timestamp || 'N/A'}</td>
        <td><span class="badge">${entry.category || 'GENERAL'}</span></td>
        <td>${entry.description || ''}</td>
        <td><code>${entry.filePath || ''}</code></td>
        <td><span style="color: var(--success); font-weight:600;">PASSED</span></td>
        <td><code>${entry.commitHash ? entry.commitHash.substring(0, 7) : 'pending'}</code></td>
      `;
      this.historyTableBody.appendChild(row);
    });
  }
}
