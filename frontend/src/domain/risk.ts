import type { Finding, Severity } from './types';

export function severityForScore(score: number): Severity {
  if (!Number.isInteger(score) || score < 1 || score > 25) throw new RangeError('Risk score must be an integer from 1 to 25');
  if (score <= 5) return 'LOW';
  if (score <= 11) return 'MEDIUM';
  if (score <= 19) return 'HIGH';
  return 'CRITICAL';
}

export function calculateRisk(impact: number, likelihood: number) {
  if (![impact, likelihood].every((value) => Number.isInteger(value) && value >= 1 && value <= 5)) {
    throw new RangeError('Impact and likelihood must be integers from 1 to 5');
  }
  const score = impact * likelihood;
  return { score, severity: severityForScore(score) };
}

const severityRank: Record<Severity, number> = { LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4 };

export function prioritizeFindings(findings: Finding[], assetsById: Map<string, { criticality: string }>, today = new Date()) {
  return [...findings].sort((a, b) => {
    const bySeverity = severityRank[b.severity] - severityRank[a.severity];
    if (bySeverity) return bySeverity;
    if (b.score !== a.score) return b.score - a.score;
    const bSafety = assetsById.get(b.assetId)?.criticality === 'SAFETY_CRITICAL' ? 1 : 0;
    const aSafety = assetsById.get(a.assetId)?.criticality === 'SAFETY_CRITICAL' ? 1 : 0;
    if (bSafety !== aSafety) return bSafety - aSafety;
    const aOverdue = a.dueDate && new Date(a.dueDate) < today ? 1 : 0;
    const bOverdue = b.dueDate && new Date(b.dueDate) < today ? 1 : 0;
    if (aOverdue !== bOverdue) return bOverdue - aOverdue;
    return new Date(a.raisedAt).getTime() - new Date(b.raisedAt).getTime();
  });
}

export function neutralizeCsvCell(value: unknown): string {
  const text = String(value ?? '');
  const safe = /^[=+\-@]/.test(text) ? `'${text}` : text;
  return /[",\n]/.test(safe) ? `"${safe.replaceAll('"', '""')}"` : safe;
}
