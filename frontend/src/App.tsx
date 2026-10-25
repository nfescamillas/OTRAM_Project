import { useEffect, useMemo, useState, type FormEvent } from 'react';
import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowLeft, ArrowRight, Box,
  Building2, Check, ChevronRight, ClipboardCheck, Clock3, FileBarChart,
  Gauge, HardDrive, LayoutDashboard, ListChecks, LogOut, Menu, Plus, Search, ShieldAlert,
  ShieldCheck, SlidersHorizontal, UserRound, Wrench, X
} from 'lucide-react';
import type { Asset, AssetFilters, AuditEvent, DashboardSummary, Finding, NewAssetInput, RemediationAction, Site } from './domain/types';
import { otarmService } from './services/httpOtarmService';
import { ServiceError, type AuthSession, type Role } from './services/otarmService';

type Page = 'dashboard' | 'assets' | 'findings' | 'remediation' | 'reports' | 'audit';
type Toast = { id: number; text: string };

const pageTitles: Record<Page, { title: string; eyebrow: string; subtitle: string }> = {
  dashboard: { title:'Operational risk, made legible.', eyebrow:'CONTROL CENTER', subtitle:'A verified view of assets, evidence, and actions across your OT environment.' },
  assets: { title:'Asset inventory', eyebrow:'INVENTORY', subtitle:'Trace ownership, lifecycle evidence, and risk context for every registered asset.' },
  findings: { title:'Risk register', eyebrow:'RISK MANAGEMENT', subtitle:'Prioritized, explainable findings — kept separate from accepted and mitigated risk.' },
  remediation: { title:'Treatment actions', eyebrow:'REMEDIATION', subtitle:'Track accountable owners, due dates, and independent verification.' },
  reports: { title:'Reports & exports', eyebrow:'ASSURANCE', subtitle:'Create filtered, spreadsheet-safe extracts for review and governance.' },
  audit: { title:'Audit trail', eyebrow:'GOVERNANCE', subtitle:'Append-only evidence of access decisions and material business changes.' }
};

const navItems = [
  { page:'dashboard' as Page, label:'Dashboard', icon:LayoutDashboard },
  { page:'assets' as Page, label:'Asset inventory', icon:HardDrive },
  { page:'findings' as Page, label:'Risk assessment', icon:ShieldAlert },
  { page:'remediation' as Page, label:'Remediation', icon:ListChecks },
  { page:'reports' as Page, label:'Reports', icon:FileBarChart }
];

const fmt = (value: string) => value.toLowerCase().replaceAll('_',' ').replace(/\b\w/g, (c) => c.toUpperCase());
const shortDate = (value?: string) => value ? new Intl.DateTimeFormat('en',{ month:'short', day:'numeric', year:'numeric' }).format(new Date(`${value}T00:00:00`)) : '—';
const siteName = (sites: Site[], id: string) => sites.find((site) => site.id === id)?.name ?? 'Unknown site';
const errorMessage = (reason: unknown) => reason instanceof Error ? reason.message : 'The requested data could not be loaded.';
const downloadCsv = (csv:string, filename:string) => { const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const anchor=document.createElement('a');anchor.href=url;anchor.download=filename;anchor.click();window.setTimeout(()=>URL.revokeObjectURL(url),0); };

function Badge({ value, tone }: { value:string; tone?:string }) {
  const slug = (tone ?? value).toLowerCase().replaceAll('_','-');
  return <span className={`badge badge-${slug}`}><i />{fmt(value)}</span>;
}

function SignIn({ onSignedIn }: { onSignedIn:(session:AuthSession)=>void }) {
  const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  const submit=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();setBusy(true);setError('');const fd=new FormData(e.currentTarget);try{onSignedIn(await otarmService.login({email:String(fd.get('email')),password:String(fd.get('password'))}));}catch(err){setError(err instanceof Error?err.message:'Sign in failed.');setBusy(false);}};
  return <main className="login-shell"><section className="login-card"><div className="login-brand"><div className="brand-mark"><Gauge size={20}/></div><div><strong>OTARM</strong><span>ASSET & RISK MANAGER</span></div></div><span className="eyebrow">AUTHENTICATED WORKSPACE</span><h1>Sign in to OTARM</h1><p>Use one of the fictional demo accounts and the password supplied when the backend was started.</p><form onSubmit={submit}><label>Email address<input name="email" type="email" defaultValue="admin@otarm.demo" autoComplete="username" required/></label><label>Password<input name="password" type="password" autoComplete="current-password" required autoFocus/></label>{error&&<div className="form-error"><AlertTriangle size={16}/>{error}</div>}<button className="button primary" disabled={busy}>{busy?'Signing in…':'Sign in'}</button></form><small className="login-note">Demo users: admin, assessor, approver, or viewer at <span className="mono">@otarm.demo</span>.</small></section></main>;
}

function App() {
  const [session, setSession] = useState<AuthSession | null>(() => otarmService.getSession());
  const [page, setPage] = useState<Page>('dashboard');
  const [siteId, setSiteId] = useState('');
  const [sites, setSites] = useState<Site[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [assetDetail, setAssetDetail] = useState<Asset | null>(null);

  const notify = (text: string) => {
    const id = Date.now(); setToasts((items) => [...items, { id, text }]);
    window.setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 3200);
  };
  useEffect(() => { if(session) otarmService.getSites().then(setSites).catch((reason:unknown)=>{if(reason instanceof ServiceError&&reason.code==='UNAUTHENTICATED'){otarmService.logout();setSession(null);}else{notify(errorMessage(reason));}}); }, [session]);
  const navigate = (next: Page) => { setAssetDetail(null); setPage(next); setSidebarOpen(false); window.scrollTo({ top:0, behavior:'smooth' }); };
  const meta = pageTitles[page];

  if (!session) return <SignIn onSignedIn={setSession}/>;
  const initials = session.user.displayName.split(/\s+/).map((part)=>part[0]).join('').slice(0,2).toUpperCase();
  const canViewAudit = session.user.role === 'ADMIN' || session.user.role === 'APPROVER';

  return <div className="app-shell">
    <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
      <div className="brand"><div className="brand-mark"><Gauge size={20}/></div><div><strong>OTARM</strong><span>ASSET & RISK MANAGER</span></div></div>
      <div className="demo-label"><span>DEMO WORKSPACE</span><small>Fictional data only</small></div>
      <nav aria-label="Primary navigation">
        <p>WORKSPACE</p>
        {navItems.filter(item=>item.page!=='reports'||session.user.role!=='VIEWER').map(({ page: itemPage, label, icon:Icon }) => <button key={itemPage} onClick={() => navigate(itemPage)} className={page === itemPage ? 'active' : ''}><Icon size={18}/><span>{label}</span></button>)}
        <p>GOVERNANCE</p>
        {canViewAudit&&<button onClick={() => navigate('audit')} className={page === 'audit' ? 'active' : ''}><Activity size={18}/><span>Audit trail</span></button>}
      </nav>
      <div className="sidebar-bottom">
        <button className="workspace" onClick={()=>{otarmService.logout();setSession(null);}} title="Sign out"><div className="avatar">{initials}</div><span><strong>{session.user.displayName}</strong><small>{fmt(session.user.role)} · Northwind Energy</small></span><LogOut size={15}/></button>
      </div>
    </aside>
    {sidebarOpen && <button className="scrim" onClick={() => setSidebarOpen(false)} aria-label="Close menu"/>}

    <main>
      <header className="topbar">
        <button className="mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open menu"><Menu/></button>
        <div className="breadcrumb"><span>Northwind Energy</span><ChevronRight size={14}/><strong>{page === 'dashboard' ? 'Dashboard' : meta.title}</strong></div>
        <div className="top-actions"><span className="environment"><i/> API CONNECTED</span><span className="role-pill"><ShieldCheck size={15}/> {fmt(session.user.role)}</span></div>
      </header>
      <section className="content">
        <div className="page-heading">
          {assetDetail ? <button className="back" onClick={() => setAssetDetail(null)}><ArrowLeft size={16}/> Back to inventory</button> : <span className="eyebrow">{meta.eyebrow}</span>}
          {!assetDetail && <><h1>{meta.title}</h1><p>{meta.subtitle}</p></>}
        </div>
        {page === 'dashboard' && <Dashboard sites={sites} siteId={siteId} setSiteId={setSiteId} navigate={navigate}/>} 
        {page === 'assets' && (assetDetail ? <AssetDetail asset={assetDetail} sites={sites}/> : <Assets sites={sites} siteId={siteId} setSiteId={setSiteId} openAsset={setAssetDetail} notify={notify} role={session.user.role}/>)}
        {page === 'findings' && <Findings sites={sites} siteId={siteId} setSiteId={setSiteId}/>}
        {page === 'remediation' && <Remediation notify={notify} role={session.user.role}/>}
        {page === 'reports' && <Reports sites={sites} notify={notify}/>}
        {page === 'audit' && <Audit/>}
      </section>
    </main>
    <div className="toast-stack">{toasts.map((toast) => <div className="toast" key={toast.id}><Check size={16}/>{toast.text}</div>)}</div>
  </div>;
}

function Dashboard({ sites, siteId, setSiteId, navigate }: { sites:Site[]; siteId:string; setSiteId:(v:string)=>void; navigate:(p:Page)=>void }) {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = () => { setLoading(true); setError(''); otarmService.getDashboardSummary(siteId || undefined).then(setData).catch((reason:unknown) => setError(errorMessage(reason))).finally(() => setLoading(false)); };
  useEffect(load, [siteId]);
  if (loading) return <Skeleton/>;
  if (error || !data) return <ErrorState message={error || 'Dashboard data is unavailable.'} retry={load}/>;
  const totalOpen = Object.values(data.severityCounts).reduce((a,b) => a+b, 0);
  const maxSeverity = Math.max(1, ...Object.values(data.severityCounts));
  const asOf = new Intl.DateTimeFormat('en', { month:'short', day:'numeric', year:'numeric' }).format(new Date());
  return <>
    <div className="toolbar dashboard-toolbar"><div className="scope"><Building2 size={17}/><label>Site scope</label><select value={siteId} onChange={(e) => setSiteId(e.target.value)}><option value="">All operating sites</option>{sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></div><span className="as-of"><Clock3 size={15}/> As of {asOf}</span></div>
    <div className="kpi-grid">
      <Kpi icon={Box} label="Active assets" value={data.activeAssets} detail={`${sites.length} sites in scope`} tone="blue" onClick={() => navigate('assets')}/>
      <Kpi icon={ClipboardCheck} label="Assessment coverage" value={data.coveragePercent === null ? 'N/A' : `${data.coveragePercent}%`} detail={`${data.assessedAssets} of ${data.activeAssets} assets`} tone="green" progress={data.coveragePercent ?? 0}/>
      <Kpi icon={ShieldAlert} label="Open findings" value={totalOpen} detail={`${data.severityCounts.CRITICAL} critical · ${data.severityCounts.HIGH} high`} tone="red" onClick={() => navigate('findings')}/>
      <Kpi icon={Clock3} label="Overdue actions" value={data.overdueActions} detail="Require owner follow-up" tone="amber" onClick={() => navigate('remediation')}/>
    </div>
    <div className="dashboard-grid">
      <section className="panel risk-distribution"><PanelHead title="Open risk by severity" subtitle="Confirmed, unaccepted findings" action="View register" onClick={() => navigate('findings')}/><div className="bars">{(['CRITICAL','HIGH','MEDIUM','LOW'] as const).map((severity) => <div className="bar-row" key={severity}><span>{fmt(severity)}</span><div><i className={`bar ${severity.toLowerCase()}`} style={{ width:`${Math.max(4, data.severityCounts[severity] / maxSeverity * 100)}%` }}/></div><strong>{data.severityCounts[severity]}</strong></div>)}</div><div className="callout"><AlertTriangle size={17}/><span><strong>{data.lifecycleUnresolved} assets</strong> have unknown or ended lifecycle evidence.</span><button onClick={() => navigate('assets')}>Review <ArrowRight size={14}/></button></div></section>
      <section className="panel coverage-panel"><PanelHead title="Inventory assurance" subtitle="Evidence quality across active assets"/><div className="coverage-register"><div className="coverage-value"><strong>{data.coveragePercent ?? 0}%</strong><span>assessment coverage</span></div><div className="coverage-track" aria-label={`${data.coveragePercent ?? 0}% assessed`}><i style={{width:`${data.coveragePercent ?? 0}%`}}/></div><div className="coverage-rows"><div><span>Finalized assessment</span><strong>{data.assessedAssets}</strong></div><div><span>Not assessed</span><strong>{data.activeAssets-data.assessedAssets}</strong></div></div></div><div className="assurance-stats"><div><span>Lifecycle unresolved</span><strong>{data.lifecycleUnresolved}</strong></div><div><span>Accepted risks</span><strong>{data.acceptedRisks}</strong></div><div><span>Unscored findings</span><strong>{data.unscoredFindings}</strong></div></div></section>
    </div>
    <section className="panel priorities"><PanelHead title="Priority worklist" subtitle="Deterministic ranking: severity, score, safety criticality, due date, then age" action="Open risk register" onClick={() => navigate('findings')}/><div className="table-wrap"><table><thead><tr><th>#</th><th>Finding</th><th>Asset</th><th>Rating</th><th>Owner</th><th>Due</th><th></th></tr></thead><tbody>{data.topPriorities.map((finding, index) => <PriorityRow key={finding.id} finding={finding} index={index} />)}</tbody></table></div></section>
  </>;
}

function Kpi({ icon:Icon, label, value, detail, tone, progress, onClick }: any) { const content=<><span className="kpi-icon"><Icon size={20}/></span><span className="kpi-label">{label}</span><strong>{value}</strong><small>{detail}</small>{progress !== undefined && <span className="progress"><i style={{width:`${progress}%`}}/></span>}{onClick&&<ChevronRight size={18} className="kpi-arrow"/>}</>; return onClick?<button className={`kpi ${tone}`} onClick={onClick}>{content}</button>:<div className={`kpi ${tone}`}>{content}</div>; }
function PanelHead({ title, subtitle, action, onClick }: {title:string; subtitle:string; action?:string; onClick?:()=>void}) { return <div className="panel-head"><div><h2>{title}</h2><p>{subtitle}</p></div>{action && <button onClick={onClick}>{action}<ArrowRight size={15}/></button>}</div>; }
function PriorityRow({ finding, index }: {finding:Finding; index:number}) { return <tr><td><span className="rank">{String(index+1).padStart(2,'0')}</span></td><td><strong>{finding.title}</strong><small>{finding.riskScenario}</small></td><td><strong>{finding.assetId.toUpperCase()}</strong><small>Operational asset</small></td><td><Badge value={finding.severity}/><span className="score">{finding.score}</span></td><td>{finding.owner}</td><td><span className={finding.dueDate && new Date(finding.dueDate) < new Date() ? 'overdue' : ''}>{shortDate(finding.dueDate)}</span></td><td><ChevronRight size={17}/></td></tr>; }

function Assets({ sites, siteId, setSiteId, openAsset, notify, role }: {sites:Site[];siteId:string;setSiteId:(v:string)=>void;openAsset:(a:Asset)=>void;notify:(s:string)=>void;role:Role}) {
  const [assets, setAssets] = useState<Asset[]>([]); const [loading,setLoading] = useState(true); const [error,setError] = useState(''); const [search,setSearch] = useState(''); const [type,setType] = useState(''); const [lifecycle,setLifecycle] = useState(''); const [showCreate,setShowCreate] = useState(false);
  const filters = useMemo(() => ({ search, siteId, type, lifecycle }) as AssetFilters,[search,siteId,type,lifecycle]);
  const load = () => { setLoading(true); setError(''); otarmService.listAssets(filters).then(setAssets).catch((reason:unknown)=>setError(errorMessage(reason))).finally(() => setLoading(false)); };
  useEffect(load,[filters]);
  const exportCsv = async () => { try { const csv = await otarmService.exportAssetsCsv(filters); downloadCsv(csv,'otarm-assets.csv'); notify('Asset export generated safely.'); } catch(reason) { notify(errorMessage(reason)); } };
  const canCreate=role==='ADMIN'||role==='ASSESSOR'; const canExport=role!=='VIEWER';
  return <><div className="toolbar inventory-toolbar"><div className="search"><Search size={17}/><input aria-label="Search assets" placeholder="Search tag, name, vendor, model…" value={search} onChange={(e)=>setSearch(e.target.value)}/>{search && <button onClick={()=>setSearch('')}><X size={15}/></button>}</div><select aria-label="Filter by site" value={siteId} onChange={(e)=>setSiteId(e.target.value)}><option value="">All sites</option>{sites.map(s=><option value={s.id} key={s.id}>{s.name}</option>)}</select><select aria-label="Filter by type" value={type} onChange={(e)=>setType(e.target.value)}><option value="">All types</option><option value="PLC">PLC</option><option value="HMI">HMI</option><option value="FIREWALL">Firewall</option><option value="ENGINEERING_WORKSTATION">Engineering workstation</option></select><select aria-label="Filter by lifecycle" value={lifecycle} onChange={(e)=>setLifecycle(e.target.value)}><option value="">All lifecycle states</option><option value="UNKNOWN">Unknown</option><option value="END_OF_SUPPORT">End of support</option><option value="END_OF_LIFE">End of life</option></select>{canExport&&<button className="button secondary" onClick={exportCsv}><ArrowDownToLine size={16}/>Export</button>}{canCreate&&<button className="button primary" onClick={()=>setShowCreate(true)}><Plus size={17}/>Register asset</button>}</div>
    <section className="panel table-panel"><div className="table-summary"><span><strong>{assets.length}</strong> assets shown</span><span><i className="dot green"/> {assets.filter(a=>a.verification==='VERIFIED').length} verified</span><span><i className="dot amber"/> {assets.filter(a=>a.verification!=='VERIFIED').length} need review</span></div><div className="table-wrap"><table className="assets-table"><thead><tr><th>Asset</th><th>Type</th><th>Site / area</th><th>Criticality</th><th>Lifecycle</th><th>Evidence</th><th></th></tr></thead><tbody>{loading ? <tr><td colSpan={7}><div className="loading-line"/></td></tr> : assets.map(asset=><tr key={asset.id} onClick={()=>openAsset(asset)}><td><strong>{asset.name}</strong><small className="mono">{asset.tag}</small></td><td><span className="type-icon"><Wrench size={15}/></span>{fmt(asset.type)}</td><td><strong>{siteName(sites,asset.siteId)}</strong><small>{asset.area}</small></td><td><Badge value={asset.criticality}/></td><td><Badge value={asset.lifecycle}/></td><td><Badge value={asset.verification}/><small>{shortDate(asset.lastVerifiedAt)}</small></td><td><ChevronRight size={17}/></td></tr>)}</tbody></table>{!loading && !error && !assets.length && <EmptyState title="No assets match these filters" text="Clear a filter or register a new asset."/>}</div></section>
    {error&&<ErrorState message={error} retry={load}/>} {showCreate && <CreateAssetModal sites={sites} close={()=>setShowCreate(false)} done={(asset)=>{setShowCreate(false);notify(`${asset.tag} registered.`);load();}}/>}</>;
}

function CreateAssetModal({sites,close,done}:{sites:Site[];close:()=>void;done:(a:Asset)=>void}) {
  const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  const submit=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();setBusy(true);setError('');const fd=new FormData(e.currentTarget);const input:NewAssetInput={tag:String(fd.get('tag')),name:String(fd.get('name')),type:fd.get('type') as Asset['type'],siteId:String(fd.get('site')),area:String(fd.get('area')),vendor:String(fd.get('vendor')),model:String(fd.get('model')),criticality:fd.get('criticality') as Asset['criticality'],lifecycle:'UNKNOWN',verification:'UNVERIFIED',operationalStatus:'ACTIVE',owner:String(fd.get('owner')),assessed:false};try{done(await otarmService.createAsset(input));}catch(err){setError(err instanceof Error?err.message:'Could not create asset');setBusy(false);}};
  return <div className="modal-backdrop"><div className="modal" role="dialog" aria-modal="true" aria-labelledby="asset-modal"><div className="modal-head"><div><span className="eyebrow">NEW INVENTORY RECORD</span><h2 id="asset-modal">Register an OT asset</h2><p>Record facts only. OTARM will never connect to this equipment.</p></div><button onClick={close} aria-label="Close"><X/></button></div><form onSubmit={submit}><div className="form-grid"><label>Asset tag<input name="tag" required placeholder="e.g. NPR-PLC-015"/></label><label>Display name<input name="name" required placeholder="Descriptive asset name"/></label><label>Site<select name="site" required>{sites.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label><label>Area<input name="area" required placeholder="e.g. Utilities"/></label><label>Asset type<select name="type"><option value="PLC">PLC</option><option value="HMI">HMI</option><option value="SCADA_SERVER">SCADA server</option><option value="ENGINEERING_WORKSTATION">Engineering workstation</option><option value="NETWORK_SWITCH">Network switch</option><option value="FIREWALL">Firewall</option><option value="OTHER">Other</option></select></label><label>Criticality<select name="criticality"><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="SAFETY_CRITICAL">Safety critical</option><option value="LOW">Low</option></select></label><label>Vendor<input name="vendor" placeholder="Manufacturer"/></label><label>Model<input name="model" placeholder="Model / family"/></label><label className="span-2">Owner<input name="owner" placeholder="Accountable asset owner"/></label></div>{error&&<div className="form-error"><AlertTriangle size={16}/>{error}</div>}<div className="modal-actions"><button type="button" className="button secondary" onClick={close}>Cancel</button><button className="button primary" disabled={busy}>{busy?'Registering…':'Register asset'}</button></div></form></div></div>;
}

function AssetDetail({asset,sites}:{asset:Asset;sites:Site[]}) { return <><div className="asset-hero"><div className="asset-symbol"><HardDrive size={24}/></div><div><div className="asset-title-line"><h1>{asset.name}</h1><Badge value={asset.operationalStatus}/></div><p className="mono">{asset.tag} / {fmt(asset.type)}</p></div></div><div className="detail-grid"><section className="panel detail-card"><PanelHead title="Identity & technical specification" subtitle="Authoritative inventory record"/><dl><div><dt>Asset identifier</dt><dd className="mono">{asset.tag}</dd></div><div><dt>Equipment class</dt><dd>{fmt(asset.type)}</dd></div><div><dt>Site</dt><dd>{siteName(sites,asset.siteId)}</dd></div><div><dt>Area</dt><dd>{asset.area}</dd></div><div><dt>Manufacturer</dt><dd>{asset.vendor}</dd></div><div><dt>Model</dt><dd className="mono">{asset.model}</dd></div><div><dt>Firmware / OS</dt><dd className="mono">{asset.firmware||'Not recorded'}</dd></div><div><dt>Accountable owner</dt><dd>{asset.owner||'Not assigned'}</dd></div><div><dt>Network zone</dt><dd>{asset.networkZone||'Not recorded'}</dd></div><div><dt>IP address</dt><dd className="mono">{asset.ipAddress||'Not recorded'}</dd></div></dl></section><section className="panel detail-card assurance-card"><PanelHead title="Risk & assurance posture" subtitle="Current verified state"/><div className="signal"><span>Asset criticality</span><Badge value={asset.criticality}/><small>Operational consequence classification</small></div><div className="signal"><span>Inventory evidence</span><Badge value={asset.verification}/><small>Reviewed {shortDate(asset.lastVerifiedAt)}</small></div><div className="signal"><span>Lifecycle support</span><Badge value={asset.lifecycle}/><small>Human-verified vendor evidence only</small></div><div className="signal"><span>Baseline assessment</span><Badge value={asset.assessed?'FINALIZED':'NOT_ASSESSED'} tone={asset.assessed?'verified':'unknown'}/><small>{asset.assessed?'Current assessment is on record':'No security conclusion can be drawn'}</small></div></section></div></>; }

function Findings({sites,siteId,setSiteId}:{sites:Site[];siteId:string;setSiteId:(s:string)=>void}) { const [items,setItems]=useState<Finding[]>([]);const [severity,setSeverity]=useState('');const [status,setStatus]=useState('');const [loading,setLoading]=useState(true);const [error,setError]=useState('');const load=()=>{setLoading(true);setError('');otarmService.listFindings({siteId:siteId||undefined,severity:severity||undefined,status:status||undefined}).then(setItems).catch((reason:unknown)=>setError(errorMessage(reason))).finally(()=>setLoading(false))};useEffect(load,[siteId,severity,status]);return <><div className="toolbar"><select aria-label="Filter findings by site" value={siteId} onChange={e=>setSiteId(e.target.value)}><option value="">All sites</option>{sites.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><select aria-label="Filter findings by severity" value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">All severities</option>{['CRITICAL','HIGH','MEDIUM','LOW'].map(x=><option key={x}>{x}</option>)}</select><select aria-label="Filter findings by status" value={status} onChange={e=>setStatus(e.target.value)}><option value="">All statuses</option>{['OPEN','TREATMENT_IN_PROGRESS','ACCEPTED','MITIGATED'].map(x=><option key={x}>{x}</option>)}</select></div>{loading?<Skeleton/>:error?<ErrorState message={error} retry={load}/>:<div className="finding-list">{items.map(f=><article className="finding-card" key={f.id}><div className={`risk-number ${f.severity.toLowerCase()}`}><strong>{f.score}</strong><span>{f.severity}</span></div><div className="finding-main"><div className="finding-top"><span className="mono">{f.id.toUpperCase()} · {f.assetId.toUpperCase()}</span><Badge value={f.status}/></div><h2>{f.title}</h2><p>{f.riskScenario}</p><div className="finding-meta"><span><UserRound size={14}/>{f.owner||'Unassigned'}</span><span className={f.dueDate&&new Date(`${f.dueDate}T00:00:00`)<new Date()?'overdue':''}><Clock3 size={14}/>Due {shortDate(f.dueDate)}</span><span><Gauge size={14}/>Impact {f.impact} × Likelihood {f.likelihood}</span></div></div></article>)}{!items.length&&<section className="panel"><EmptyState title="No findings match" text="Try widening the site, status, or severity filter."/></section>}</div>}</>; }

function Remediation({notify,role}:{notify:(s:string)=>void;role:Role}) {
  const [items,setItems]=useState<RemediationAction[]>([]); const [assets,setAssets]=useState<Asset[]>([]); const [findings,setFindings]=useState<Finding[]>([]);
  const [loading,setLoading]=useState(true); const [error,setError]=useState('');
  const load=()=>{setLoading(true);setError('');return Promise.all([otarmService.listRemediation(),otarmService.listAssets(),otarmService.listFindings()]).then(([nextItems,nextAssets,nextFindings])=>{setItems(nextItems);setAssets(nextAssets);setFindings(nextFindings)}).catch((reason:unknown)=>setError(errorMessage(reason))).finally(()=>setLoading(false))};
  useEffect(()=>{void load()},[]);
  const relatedAsset=(action:RemediationAction)=>{const finding=findings.find(f=>f.id===action.findingId);return assets.find(a=>a.id===finding?.assetId)};
  const advance=async(a:RemediationAction)=>{const next:Partial<Record<RemediationAction['status'],RemediationAction['status']>>={OPEN:'PLANNED',PLANNED:'IN_PROGRESS',IN_PROGRESS:'PENDING_VERIFICATION',PENDING_VERIFICATION:'VERIFIED'};const target=next[a.status];if(!target)return;try{await otarmService.updateActionStatus(a.id,target);notify(`Action moved to ${fmt(target)}.`);await load();}catch(reason){notify(errorMessage(reason));}};
  if(loading)return <Skeleton/>; if(error)return <ErrorState message={error} retry={load}/>;
  return <><div className="work-register"><div><span>Open / planned</span><strong>{items.filter(a=>['OPEN','PLANNED'].includes(a.status)).length}</strong></div><div><span>In progress</span><strong>{items.filter(a=>a.status==='IN_PROGRESS').length}</strong></div><div><span>Awaiting verification</span><strong>{items.filter(a=>a.status==='PENDING_VERIFICATION').length}</strong></div><div><span>Past due</span><strong>{items.filter(a=>new Date(`${a.dueDate}T00:00:00`)<new Date()&&!['VERIFIED','CANCELLED'].includes(a.status)).length}</strong></div></div><section className="panel table-panel"><div className="workflow-note"><ShieldCheck size={18}/><div><strong>Independent verification is enforced by the service.</strong><span>An assignee may submit work, but cannot verify their own action.</span></div></div><div className="table-wrap"><table><thead><tr><th>Action / reference</th><th>Related asset</th><th>Owner</th><th>Due date</th><th>Workflow status</th><th>Next step</th></tr></thead><tbody>{items.map(a=>{const asset=relatedAsset(a);const canAdvance=role!=='VIEWER'&&!['VERIFIED','CANCELLED'].includes(a.status)&&(a.status!=='PENDING_VERIFICATION'||role==='ADMIN'||role==='APPROVER');return <tr key={a.id}><td><strong>{a.title}</strong><small className="mono">{a.id.toUpperCase()} / {a.findingId.toUpperCase()}</small></td><td><strong>{asset?.name??'Unknown asset'}</strong><small className="mono">{asset?.tag??'—'}</small></td><td>{a.assignedTo}</td><td><span className={new Date(`${a.dueDate}T00:00:00`)<new Date()&&!['VERIFIED','CANCELLED'].includes(a.status)?'overdue':''}>{shortDate(a.dueDate)}</span></td><td><Badge value={a.status}/></td><td>{canAdvance?<button className="text-button" onClick={()=>advance(a)}>{a.status==='PENDING_VERIFICATION'?'Verify independently':'Advance workflow'}<ArrowRight size={14}/></button>:<span className="muted">{a.status==='PENDING_VERIFICATION'&&role==='ASSESSOR'?'Awaiting approver':'—'}</span>}</td></tr>})}</tbody></table></div></section></>;
}

function Reports({sites,notify}:{sites:Site[];notify:(s:string)=>void}) { const [siteId,setSiteId]=useState('');const [busy,setBusy]=useState(false);const exportReport=async()=>{setBusy(true);try{const csv=await otarmService.exportAssetsCsv({siteId:siteId||undefined});downloadCsv(csv,'otarm-assets.csv');notify('Asset inventory report generated.');}catch(reason){notify(errorMessage(reason));}finally{setBusy(false)}};return <div className="report-grid"><section className="panel report-builder"><PanelHead title="Export asset inventory" subtitle="Filters are applied through the same scoped service boundary"/><div className="report-types single"><div className="active"><HardDrive size={20}/><span><strong>Asset inventory</strong><small>CSV · organization scoped</small></span><Check size={17}/></div></div><div className="report-filters"><label>Site<select value={siteId} onChange={event=>setSiteId(event.target.value)}><option value="">All operating sites</option>{sites.map(s=><option value={s.id} key={s.id}>{s.name}</option>)}</select></label></div><button className="button primary wide" onClick={exportReport} disabled={busy}><ArrowDownToLine size={17}/>{busy?'Generating…':'Generate safe CSV export'}</button></section><aside className="panel report-info"><span className="report-icon"><ShieldCheck/></span><h2>Export safeguards</h2><p>Every generated file is scoped to the signed-in organization and neutralizes spreadsheet formula characters.</p><ul><li><Check size={15}/>Selected site filter is preserved</li><li><Check size={15}/>UTF-8 CSV formatting</li><li><Check size={15}/>No hidden inventory fields</li></ul></aside></div>; }

function Audit() { const [items,setItems]=useState<AuditEvent[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');const load=()=>{setLoading(true);setError('');otarmService.getAuditEvents().then(setItems).catch((reason:unknown)=>setError(errorMessage(reason))).finally(()=>setLoading(false))};useEffect(load,[]);if(loading)return <Skeleton/>;if(error)return <ErrorState message={error} retry={load}/>;return <section className="panel table-panel"><div className="workflow-note"><Activity size={18}/><div><strong>Application business audit history</strong><span>Recorded asset and treatment changes are retained in chronological order.</span></div></div><div className="table-wrap"><table><thead><tr><th>Occurred</th><th>Actor</th><th>Action</th><th>Object</th><th>Result</th></tr></thead><tbody>{items.map(e=><tr key={e.id}><td>{new Date(e.occurredAt).toLocaleString()}</td><td><strong>{e.actor}</strong></td><td className="mono">{e.action}</td><td>{e.entity}</td><td><Badge value={e.result}/></td></tr>)}</tbody></table></div></section>; }

function EmptyState({title,text}:{title:string;text:string}) { return <div className="empty"><SlidersHorizontal size={26}/><strong>{title}</strong><p>{text}</p></div>; }
function ErrorState({message,retry}:{message:string;retry:()=>unknown}) { return <section className="panel error-state" role="alert"><AlertTriangle size={22}/><div><strong>Unable to load this view</strong><p>{message}</p></div><button className="button secondary" onClick={()=>retry()}>Try again</button></section>; }
function Skeleton() { return <div className="skeleton"><div/><div/><div/><div/></div>; }

export default App;
