import { beforeEach, describe, expect, it } from 'vitest';
import { MockOtarmService } from './mockOtarmService';

describe('MockOtarmService', () => {
  let service: MockOtarmService;
  beforeEach(() => { service = new MockOtarmService(); });

  it('applies asset filters inside the service layer', async () => {
    const items = await service.listAssets({ siteId:'site-water', type:'PLC', search:'chemical' });
    expect(items).toHaveLength(1);
    expect(items[0].tag).toBe('WTP-PLC-021');
  });

  it('rejects duplicate asset tags', async () => {
    const existing = await service.getAsset('a1');
    const { id: _id, assessed: _assessed, ...input } = existing;
    await expect(service.createAsset(input)).rejects.toMatchObject({ code:'CONFLICT' });
  });

  it('returns detached values so callers cannot mutate service state', async () => {
    const items = await service.listAssets();
    items[0].name = 'Tampered';
    expect((await service.getAsset('a1')).name).toBe('Boiler Feedwater PLC');
  });

  it('calculates dashboard counts for site scope', async () => {
    const summary = await service.getDashboardSummary('site-water');
    expect(summary.activeAssets).toBe(3);
    expect(summary.assessedAssets).toBe(1);
    expect(summary.severityCounts.HIGH).toBe(1);
  });

  it('exports a scoped CSV with stable headers', async () => {
    const csv = await service.exportAssetsCsv({ siteId:'site-terminal' });
    expect(csv.split('\n')).toHaveLength(3);
    expect(csv).toContain('Asset tag,Name,Type,Site,Criticality,Lifecycle,Owner');
    expect(csv).not.toContain('NPR-PLC-014');
  });
});
