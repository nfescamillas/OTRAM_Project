export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Criticality = 'LOW' | 'MEDIUM' | 'HIGH' | 'SAFETY_CRITICAL';
export type LifecycleState = 'UNKNOWN' | 'SUPPORTED' | 'LIMITED_SUPPORT' | 'END_OF_SUPPORT' | 'END_OF_LIFE';
export type AssetType = 'PLC' | 'DCS_SERVER' | 'SCADA_SERVER' | 'ENGINEERING_WORKSTATION' | 'HMI' | 'NETWORK_SWITCH' | 'FIREWALL' | 'ROUTER' | 'HISTORIAN' | 'GATEWAY' | 'OTHER';
export type FindingStatus = 'OPEN' | 'TREATMENT_IN_PROGRESS' | 'MITIGATED' | 'ACCEPTED';
export type ActionStatus = 'OPEN' | 'PLANNED' | 'IN_PROGRESS' | 'PENDING_VERIFICATION' | 'VERIFIED' | 'CANCELLED';

export interface Site { id: string; code: string; name: string; }
export interface Asset {
  id: string; tag: string; name: string; type: AssetType; siteId: string; area: string;
  vendor: string; model: string; criticality: Criticality; lifecycle: LifecycleState;
  verification: 'VERIFIED' | 'UNVERIFIED' | 'STALE'; lastVerifiedAt?: string;
  operationalStatus: 'ACTIVE' | 'STANDBY' | 'OUT_OF_SERVICE' | 'RETIRED'; owner?: string;
  firmware?: string; networkZone?: string; ipAddress?: string; assessed: boolean;
}
export interface Finding {
  id: string; assetId: string; title: string; riskScenario: string; controlGap: string;
  recommendedTreatment: string; status: FindingStatus; impact: number; likelihood: number;
  severity: Severity; score: number; raisedAt: string; dueDate?: string; owner?: string;
}
export interface RemediationAction {
  id: string; findingId: string; title: string; assignedTo: string; dueDate: string;
  status: ActionStatus; completionNotes?: string;
}
export interface AuditEvent { id: string; actor: string; action: string; entity: string; occurredAt: string; result: 'SUCCESS' | 'DENIED'; }
export interface DashboardSummary {
  activeAssets: number; assessedAssets: number; coveragePercent: number | null;
  severityCounts: Record<Severity, number>; lifecycleUnresolved: number; overdueActions: number;
  acceptedRisks: number; unscoredFindings: number; topPriorities: Finding[];
}
export interface AssetFilters { search?: string; siteId?: string; type?: AssetType | ''; lifecycle?: LifecycleState | ''; }
export interface NewAssetInput extends Omit<Asset, 'id' | 'assessed'> { assessed?: boolean; }
