import type { Asset, AssetFilters, AuditEvent, DashboardSummary, Finding, NewAssetInput, RemediationAction, Site } from '../domain/types';

export type Role = 'ADMIN' | 'ASSESSOR' | 'APPROVER' | 'VIEWER';
export interface PublicUser { id: string; email: string; displayName: string; role: Role; }
export interface AuthSession { accessToken: string; expiresAt: number; user: PublicUser; }
export interface LoginCredentials { email: string; password: string; }

export interface OtarmService {
  getSites(): Promise<Site[]>;
  getDashboardSummary(siteId?: string): Promise<DashboardSummary>;
  listAssets(filters?: AssetFilters): Promise<Asset[]>;
  getAsset(id: string): Promise<Asset>;
  createAsset(input: NewAssetInput): Promise<Asset>;
  listFindings(filters?: { siteId?: string; status?: string; severity?: string }): Promise<Finding[]>;
  listRemediation(): Promise<RemediationAction[]>;
  updateActionStatus(id: string, status: RemediationAction['status']): Promise<RemediationAction>;
  getAuditEvents(): Promise<AuditEvent[]>;
  exportAssetsCsv(filters?: AssetFilters): Promise<string>;
}

export interface AuthenticatedOtarmService extends OtarmService {
  login(credentials: LoginCredentials): Promise<AuthSession>;
  logout(): void;
  getSession(): AuthSession | null;
}

export class ServiceError extends Error {
  constructor(message: string, public readonly code: 'UNAUTHENTICATED' | 'NOT_FOUND' | 'CONFLICT' | 'FORBIDDEN' | 'VALIDATION' | 'INTERNAL') { super(message); }
}
