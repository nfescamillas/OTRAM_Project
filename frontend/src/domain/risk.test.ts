import { describe, expect, it } from 'vitest';
import { calculateRisk, neutralizeCsvCell, prioritizeFindings, severityForScore } from './risk';
import type { Finding } from './types';

describe('risk scoring policy OTARM-5X5 v1', () => {
  it.each([
    [1, 'LOW'], [5, 'LOW'], [6, 'MEDIUM'], [11, 'MEDIUM'],
    [12, 'HIGH'], [19, 'HIGH'], [20, 'CRITICAL'], [25, 'CRITICAL']
  ] as const)('maps boundary score %i to %s', (score, severity) => {
    expect(severityForScore(score)).toBe(severity);
  });

  it('calculates impact × likelihood rather than trusting a submitted score', () => {
    expect(calculateRisk(5, 4)).toEqual({ score: 20, severity: 'CRITICAL' });
  });

  it('rejects values outside the 1–5 rating scale', () => {
    expect(() => calculateRisk(0, 4)).toThrow(RangeError);
    expect(() => calculateRisk(5, 6)).toThrow(RangeError);
  });
});

describe('finding prioritization', () => {
  const base: Finding = { id:'f', assetId:'a', title:'x', riskScenario:'x', controlGap:'x', recommendedTreatment:'x', status:'OPEN', impact:3, likelihood:4, score:12, severity:'HIGH', raisedAt:'2026-01-01' };
  it('sorts by severity, score, safety criticality, overdue state, then age', () => {
    const items = [
      { ...base, id:'low', severity:'MEDIUM' as const, score:11 },
      { ...base, id:'newer', assetId:'normal', raisedAt:'2026-02-01' },
      { ...base, id:'safety', assetId:'safety', raisedAt:'2026-03-01' },
      { ...base, id:'critical', severity:'CRITICAL' as const, score:20 }
    ];
    const result = prioritizeFindings(items, new Map([['normal',{criticality:'HIGH'}],['safety',{criticality:'SAFETY_CRITICAL'}]]), new Date('2026-10-17'));
    expect(result.map((item) => item.id)).toEqual(['critical','safety','newer','low']);
  });
});

describe('CSV safety', () => {
  it.each(['=1+1','+SUM(A1:A2)','-2+3','@cmd'])('neutralizes dangerous value %s', (value) => {
    expect(neutralizeCsvCell(value).startsWith("'")).toBe(true);
  });

  it('quotes commas and escapes embedded quotes', () => {
    expect(neutralizeCsvCell('Valve, "north"')).toBe('"Valve, ""north"""');
  });
});
