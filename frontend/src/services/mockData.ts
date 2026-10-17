import type { Asset, AuditEvent, Finding, RemediationAction, Site } from '../domain/types';
import { calculateRisk } from '../domain/risk';

export const sites: Site[] = [
  { id: 'site-north', code: 'NPR', name: 'North Process Plant' },
  { id: 'site-water', code: 'WTP', name: 'West Water Plant' },
  { id: 'site-terminal', code: 'SBT', name: 'South Bulk Terminal' }
];

export const assets: Asset[] = [
  { id:'a1', tag:'NPR-PLC-014', name:'Boiler Feedwater PLC', type:'PLC', siteId:'site-north', area:'Utilities', vendor:'Rockwell Automation', model:'ControlLogix 5580', criticality:'SAFETY_CRITICAL', lifecycle:'SUPPORTED', verification:'VERIFIED', lastVerifiedAt:'2026-10-12', operationalStatus:'ACTIVE', owner:'Maya Chen', firmware:'v35.011', networkZone:'Cell 2 · Utilities', ipAddress:'10.42.20.14', assessed:true },
  { id:'a2', tag:'WTP-HMI-003', name:'Clarifier Operator HMI', type:'HMI', siteId:'site-water', area:'Clarification', vendor:'Siemens', model:'IPC477E', criticality:'HIGH', lifecycle:'END_OF_SUPPORT', verification:'STALE', lastVerifiedAt:'2025-08-04', operationalStatus:'ACTIVE', owner:'Ethan Cole', firmware:'Windows 10 LTSC 2019', networkZone:'Cell 1 · Process', ipAddress:'10.56.11.23', assessed:true },
  { id:'a3', tag:'NPR-SRV-007', name:'Historian Primary', type:'HISTORIAN', siteId:'site-north', area:'Control Room', vendor:'Dell', model:'PowerEdge R740', criticality:'HIGH', lifecycle:'LIMITED_SUPPORT', verification:'VERIFIED', lastVerifiedAt:'2026-09-21', operationalStatus:'ACTIVE', owner:'Priya Nair', firmware:'Historian 2023 R2', networkZone:'Operations DMZ', ipAddress:'10.42.40.7', assessed:true },
  { id:'a4', tag:'SBT-FW-002', name:'Terminal OT Perimeter', type:'FIREWALL', siteId:'site-terminal', area:'Main Rack', vendor:'Palo Alto Networks', model:'PA-3220', criticality:'SAFETY_CRITICAL', lifecycle:'SUPPORTED', verification:'VERIFIED', lastVerifiedAt:'2026-10-01', operationalStatus:'ACTIVE', owner:'Noah Williams', firmware:'PAN-OS 11.1.4', networkZone:'OT Perimeter', ipAddress:'10.73.0.1', assessed:true },
  { id:'a5', tag:'WTP-PLC-021', name:'Chemical Dosing PLC', type:'PLC', siteId:'site-water', area:'Chemical Dosing', vendor:'Schneider Electric', model:'Modicon M580', criticality:'SAFETY_CRITICAL', lifecycle:'UNKNOWN', verification:'UNVERIFIED', operationalStatus:'ACTIVE', owner:'', firmware:'4.10', networkZone:'Cell 3 · Dosing', ipAddress:'10.56.30.21', assessed:false },
  { id:'a6', tag:'NPR-ENG-005', name:'Turbine Engineering Station', type:'ENGINEERING_WORKSTATION', siteId:'site-north', area:'Generation', vendor:'HP', model:'Z4 G4', criticality:'HIGH', lifecycle:'END_OF_LIFE', verification:'STALE', lastVerifiedAt:'2024-11-16', operationalStatus:'ACTIVE', owner:'Maya Chen', firmware:'Windows Server 2016', networkZone:'Cell 4 · Generation', ipAddress:'10.42.44.5', assessed:true },
  { id:'a7', tag:'SBT-SW-011', name:'Jetty Access Switch', type:'NETWORK_SWITCH', siteId:'site-terminal', area:'Jetty 2', vendor:'Cisco', model:'IE-3300', criticality:'MEDIUM', lifecycle:'SUPPORTED', verification:'VERIFIED', lastVerifiedAt:'2026-07-18', operationalStatus:'ACTIVE', owner:'Noah Williams', firmware:'IOS XE 17.12', networkZone:'Cell 5 · Jetty', ipAddress:'10.73.50.11', assessed:false },
  { id:'a8', tag:'WTP-RTU-008', name:'Reservoir Telemetry Gateway', type:'GATEWAY', siteId:'site-water', area:'Remote Reservoir', vendor:'Red Lion', model:'FlexEdge DA70', criticality:'HIGH', lifecycle:'UNKNOWN', verification:'UNVERIFIED', operationalStatus:'STANDBY', owner:'Ethan Cole', firmware:'Unknown', networkZone:'Remote Sites', ipAddress:'172.22.8.10', assessed:false }
];

const finding = (data: Omit<Finding,'score'|'severity'>): Finding => ({ ...data, ...calculateRisk(data.impact, data.likelihood) });
export const findings: Finding[] = [
  finding({ id:'f1', assetId:'a1', title:'Recovery backup not restoration-tested', riskScenario:'A controller failure could extend loss of boiler feedwater control if the current backup cannot be restored.', controlGap:'No restoration test evidence for the current logic backup.', recommendedTreatment:'Perform an offline restore test and document results.', status:'OPEN', impact:5, likelihood:4, raisedAt:'2026-09-18', dueDate:'2026-10-10', owner:'Maya Chen' }),
  finding({ id:'f2', assetId:'a2', title:'Unsupported operator workstation platform', riskScenario:'Unsupported platform vulnerabilities could disrupt operator visibility for clarifier operations.', controlGap:'Vendor support ended and no approved isolation exception is recorded.', recommendedTreatment:'Upgrade platform or document compensating isolation controls.', status:'TREATMENT_IN_PROGRESS', impact:4, likelihood:4, raisedAt:'2026-08-04', dueDate:'2026-11-15', owner:'Ethan Cole' }),
  finding({ id:'f3', assetId:'a6', title:'Shared engineering credentials', riskScenario:'Unattributed engineering changes could alter turbine control logic without accountability.', controlGap:'Engineering tool uses a shared privileged account.', recommendedTreatment:'Implement named accounts and a controlled emergency credential.', status:'OPEN', impact:5, likelihood:3, raisedAt:'2026-07-11', dueDate:'2026-09-30', owner:'Maya Chen' }),
  finding({ id:'f4', assetId:'a4', title:'Remote access rule review overdue', riskScenario:'Stale vendor access rules may provide unnecessary paths into the terminal OT zone.', controlGap:'Quarterly rule recertification is 45 days overdue.', recommendedTreatment:'Complete rule owner review and remove unused entries.', status:'OPEN', impact:4, likelihood:3, raisedAt:'2026-09-01', dueDate:'2026-10-28', owner:'Noah Williams' }),
  finding({ id:'f5', assetId:'a3', title:'Historian recovery dependencies incomplete', riskScenario:'An infrastructure failure may delay restoration of operational history.', controlGap:'Recovery runbook omits identity and time-source dependencies.', recommendedTreatment:'Update and tabletop the recovery runbook.', status:'ACCEPTED', impact:3, likelihood:2, raisedAt:'2026-05-06', dueDate:'2027-02-01', owner:'Priya Nair' })
];

export const actions: RemediationAction[] = [
  { id:'r1', findingId:'f1', title:'Run offline controller restore test', assignedTo:'Maya Chen', dueDate:'2026-10-10', status:'PENDING_VERIFICATION' },
  { id:'r2', findingId:'f2', title:'Procure supported HMI platform', assignedTo:'Ethan Cole', dueDate:'2026-11-15', status:'IN_PROGRESS' },
  { id:'r3', findingId:'f3', title:'Create named engineering accounts', assignedTo:'Maya Chen', dueDate:'2026-09-30', status:'OPEN' },
  { id:'r4', findingId:'f4', title:'Recertify OT remote-access rule set', assignedTo:'Noah Williams', dueDate:'2026-10-28', status:'PLANNED' }
];

export const auditEvents: AuditEvent[] = [
  { id:'e1', actor:'Alicia Morgan', action:'ASSESSMENT_FINALIZED', entity:'NPR-PLC-014 · OT-BASELINE v1', occurredAt:'2026-10-16T06:42:00Z', result:'SUCCESS' },
  { id:'e2', actor:'Maya Chen', action:'ACTION_SUBMITTED', entity:'Run offline controller restore test', occurredAt:'2026-10-15T23:18:00Z', result:'SUCCESS' },
  { id:'e3', actor:'Jordan Lee', action:'ASSET_UPDATED', entity:'WTP-HMI-003', occurredAt:'2026-10-15T02:05:00Z', result:'SUCCESS' },
  { id:'e4', actor:'Alicia Morgan', action:'AUTHORIZATION_DENIED', entity:'Risk acceptance · f1', occurredAt:'2026-10-14T19:33:00Z', result:'DENIED' }
];
