import { neutralizeCsvCell, prioritizeFindings } from '../domain/risk';
import type { Asset, AssetFilters, AuditEvent, DashboardSummary, Finding, NewAssetInput, RemediationAction, Site } from '../domain/types';
import type { OtarmService } from './otarmService';
import { ServiceError } from './otarmService';
import { actions as seedActions, assets as seedAssets, auditEvents as seedAudit, findings as seedFindings, sites } from './mockData';

const delay = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
const copy = <T,>(value: T): T => structuredClone(value);

export class MockOtarmService implements OtarmService {
  private assets = copy(seedAssets);
  private findings = copy(seedFindings);
  private actions = copy(seedActions);
  private audit = copy(seedAudit);

  async getSites(): Promise<Site[]> { await delay(); return copy(sites); }

  async listAssets(filters: AssetFilters = {}): Promise<Asset[]> {
    await delay();
    const search = filters.search?.trim().toLowerCase();
    return copy(this.assets.filter((asset) =>
      (!filters.siteId || asset.siteId === filters.siteId) &&
      (!filters.type || asset.type === filters.type) &&
      (!filters.lifecycle || asset.lifecycle === filters.lifecycle) &&
      (!search || [asset.tag, asset.name, asset.vendor, asset.model].some((value) => value.toLowerCase().includes(search)))
    ));
  }

  async getAsset(id: string): Promise<Asset> {
    await delay(); const asset = this.assets.find((item) => item.id === id);
    if (!asset) throw new ServiceError('Asset not found', 'NOT_FOUND');
    return copy(asset);
  }

  async createAsset(input: NewAssetInput): Promise<Asset> {
    await delay();
    if (!input.tag.trim() || !input.name.trim()) throw new ServiceError('Asset tag and name are required', 'VALIDATION');
    if (this.assets.some((asset) => asset.tag.toLowerCase() === input.tag.toLowerCase())) throw new ServiceError('Asset tag already exists', 'CONFLICT');
    const asset: Asset = { ...copy(input), id: `a-${crypto.randomUUID()}`, assessed: input.assessed ?? false };
    this.assets.unshift(asset);
    this.audit.unshift({ id: `e-${crypto.randomUUID()}`, actor:'Alicia Morgan', action:'ASSET_CREATED', entity:asset.tag, occurredAt:new Date().toISOString(), result:'SUCCESS' });
    return copy(asset);
  }

  async listFindings(filters: { siteId?: string; status?: string; severity?: string } = {}): Promise<Finding[]> {
    await delay();
    const assetIds = new Set(this.assets.filter((a) => !filters.siteId || a.siteId === filters.siteId).map((a) => a.id));
    return copy(this.findings.filter((f) => assetIds.has(f.assetId) && (!filters.status || f.status === filters.status) && (!filters.severity || f.severity === filters.severity)));
  }

  async listRemediation(): Promise<RemediationAction[]> { await delay(); return copy(this.actions); }

  async updateActionStatus(id: string, status: RemediationAction['status']): Promise<RemediationAction> {
    await delay(); const action = this.actions.find((item) => item.id === id);
    if (!action) throw new ServiceError('Remediation action not found', 'NOT_FOUND');
    action.status = status;
    this.audit.unshift({ id:`e-${crypto.randomUUID()}`, actor:'Alicia Morgan', action:'ACTION_STATUS_CHANGED', entity:action.title, occurredAt:new Date().toISOString(), result:'SUCCESS' });
    return copy(action);
  }

  async getAuditEvents(): Promise<AuditEvent[]> { await delay(); return copy(this.audit); }

  async getDashboardSummary(siteId?: string): Promise<DashboardSummary> {
    await delay();
    const scopedAssets = this.assets.filter((a) => a.operationalStatus !== 'RETIRED' && (!siteId || a.siteId === siteId));
    const assetIds = new Set(scopedAssets.map((a) => a.id));
    const scopedFindings = this.findings.filter((f) => assetIds.has(f.assetId));
    const open = scopedFindings.filter((f) => f.status === 'OPEN' || f.status === 'TREATMENT_IN_PROGRESS');
    const severityCounts = { LOW:0, MEDIUM:0, HIGH:0, CRITICAL:0 };
    open.forEach((f) => severityCounts[f.severity]++);
    const actionIds = new Set(open.map((f) => f.id));
    const overdueActions = this.actions.filter((a) => actionIds.has(a.findingId) && !['VERIFIED','CANCELLED'].includes(a.status) && new Date(a.dueDate) < new Date()).length;
    const assessedAssets = scopedAssets.filter((a) => a.assessed).length;
    return {
      activeAssets: scopedAssets.length, assessedAssets,
      coveragePercent: scopedAssets.length ? Math.round(assessedAssets / scopedAssets.length * 100) : null,
      severityCounts, lifecycleUnresolved: scopedAssets.filter((a) => ['UNKNOWN','END_OF_SUPPORT','END_OF_LIFE'].includes(a.lifecycle)).length,
      overdueActions, acceptedRisks: scopedFindings.filter((f) => f.status === 'ACCEPTED').length, unscoredFindings:0,
      topPriorities: prioritizeFindings(open, new Map(scopedAssets.map((a) => [a.id, a]))).slice(0, 10)
    };
  }

  async exportAssetsCsv(filters: AssetFilters = {}): Promise<string> {
    const rows = await this.listAssets(filters);
    const header = ['Asset tag','Name','Type','Site','Criticality','Lifecycle','Owner'];
    return [header, ...rows.map((a) => [a.tag,a.name,a.type,sites.find((s) => s.id === a.siteId)?.name ?? '',a.criticality,a.lifecycle,a.owner ?? ''])]
      .map((row) => row.map(neutralizeCsvCell).join(',')).join('\n');
  }
}

export const otarmService: OtarmService = new MockOtarmService();
