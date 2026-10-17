import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import App from './App';

vi.mock('./services/httpOtarmService', () => ({
  otarmService: {
    getSession: () => ({ accessToken:'test-token', expiresAt:Date.now()+60_000, user:{ id:'u1', email:'admin@otarm.demo', displayName:'Admin User', role:'ADMIN' } }),
    getSites: vi.fn().mockResolvedValue([{ id:'site-1', code:'ONE', name:'Test Site' }]),
    getDashboardSummary: vi.fn().mockResolvedValue({ activeAssets:1, assessedAssets:1, coveragePercent:100, severityCounts:{ LOW:0, MEDIUM:0, HIGH:0, CRITICAL:0 }, lifecycleUnresolved:0, overdueActions:0, acceptedRisks:0, unscoredFindings:0, topPriorities:[] }),
    logout: vi.fn(),
  }
}));

describe('OTARM application shell', () => {
  it('loads the dashboard through the service boundary', async () => {
    render(<App />);
    expect(screen.getByRole('heading', { name:'Operational risk, made legible.' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Assessment coverage')).toBeInTheDocument());
    expect(screen.getByText('Priority worklist')).toBeInTheDocument();
    expect(screen.getByText('Fictional data only')).toBeInTheDocument();
  });
});
