import type { Asset, AssetFilters, AuditEvent, DashboardSummary, Finding, NewAssetInput, RemediationAction, Site } from '../domain/types';
import type { AuthSession, AuthenticatedOtarmService, LoginCredentials, PublicUser } from './otarmService';
import { ServiceError } from './otarmService';

type ApiError = { code?: string; message?: string };
type TokenResponse = { accessToken: string; expiresIn: number; user: PublicUser };

const SESSION_KEY = 'otarm.session';
const DEFAULT_BASE_URL = '/api/v1';

export class HttpOtarmService implements AuthenticatedOtarmService {
  constructor(
    private readonly baseUrl = import.meta.env.VITE_OTARM_API_BASE_URL || DEFAULT_BASE_URL,
    private readonly fetcher: typeof fetch = fetch,
    private readonly storage: Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> = sessionStorage,
  ) {}

  getSession(): AuthSession | null {
    const value = this.storage.getItem(SESSION_KEY);
    if (!value) return null;
    try {
      const session = JSON.parse(value) as AuthSession;
      if (!session.accessToken || !session.user || session.expiresAt <= Date.now()) {
        this.logout();
        return null;
      }
      return session;
    } catch {
      this.logout();
      return null;
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthSession> {
    const response = await this.request<TokenResponse>('/auth/token', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }, false);
    const session = {
      accessToken: response.accessToken,
      expiresAt: Date.now() + response.expiresIn * 1000,
      user: response.user,
    };
    this.storage.setItem(SESSION_KEY, JSON.stringify(session));
    return session;
  }

  logout(): void { this.storage.removeItem(SESSION_KEY); }

  getSites(): Promise<Site[]> { return this.request('/sites'); }
  getDashboardSummary(siteId?: string): Promise<DashboardSummary> { return this.request(`/dashboard/summary${this.query({ siteId })}`); }
  listAssets(filters: AssetFilters = {}): Promise<Asset[]> { return this.request(`/assets${this.query(filters)}`); }
  getAsset(id: string): Promise<Asset> { return this.request(`/assets/${encodeURIComponent(id)}`); }
  createAsset(input: NewAssetInput): Promise<Asset> { return this.request('/assets', { method: 'POST', body: JSON.stringify(input) }); }
  listFindings(filters: { siteId?: string; status?: string; severity?: string } = {}): Promise<Finding[]> { return this.request(`/findings${this.query(filters)}`); }
  listRemediation(): Promise<RemediationAction[]> { return this.request('/remediation'); }
  updateActionStatus(id: string, status: RemediationAction['status']): Promise<RemediationAction> {
    return this.request(`/actions/${encodeURIComponent(id)}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
  }
  getAuditEvents(): Promise<AuditEvent[]> { return this.request('/audit-events'); }
  exportAssetsCsv(filters: AssetFilters = {}): Promise<string> { return this.request(`/assets/export.csv${this.query(filters)}`, {}, true, 'text'); }

  private query(values: object): string {
    const params = new URLSearchParams();
    Object.entries(values).forEach(([key, value]) => { if (value !== undefined && value !== '') params.set(key, String(value)); });
    const query = params.toString();
    return query ? `?${query}` : '';
  }

  private async request<T>(path: string, init: RequestInit = {}, authenticated = true, responseType: 'json' | 'text' = 'json'): Promise<T> {
    const headers = new Headers(init.headers);
    if (init.body) headers.set('Content-Type', 'application/json');
    if (authenticated) {
      const session = this.getSession();
      if (!session) throw new ServiceError('Please sign in to continue.', 'UNAUTHENTICATED');
      headers.set('Authorization', `Bearer ${session.accessToken}`);
    }

    let response: Response;
    try {
      const fetcher = this.fetcher;
      response = await fetcher(`${this.baseUrl}${path}`, { ...init, headers });
    } catch {
      throw new ServiceError('Cannot reach the OTARM backend. Confirm that it is running and try again.', 'INTERNAL');
    }
    if (!response.ok) {
      let error: ApiError = {};
      try { error = await response.json() as ApiError; } catch { /* response was not JSON */ }
      const code = this.errorCode(error.code, response.status);
      if (code === 'UNAUTHENTICATED') this.logout();
      throw new ServiceError(error.message || `Request failed with status ${response.status}.`, code);
    }
    return (responseType === 'text' ? await response.text() : await response.json()) as T;
  }

  private errorCode(code: string | undefined, status: number): ServiceError['code'] {
    if (code === 'UNAUTHENTICATED' || status === 401) return 'UNAUTHENTICATED';
    if (code === 'FORBIDDEN' || status === 403) return 'FORBIDDEN';
    if (code === 'NOT_FOUND' || status === 404) return 'NOT_FOUND';
    if (code === 'CONFLICT' || status === 409) return 'CONFLICT';
    if (code === 'VALIDATION' || status === 400 || status === 422) return 'VALIDATION';
    return 'INTERNAL';
  }
}

export const otarmService = new HttpOtarmService();
