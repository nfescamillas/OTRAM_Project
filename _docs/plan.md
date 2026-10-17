# OTARM — OT Asset & Risk Manager
## Product Requirements Specification (PRS) v1.0
**Status:** Approved design baseline (implementation not yet started)  
**Date:** 2026-10-17  
**Product:** OT Asset & Risk Manager (OTARM)  
**Delivery:** Secure web/server-hosted application  
**Architecture:** Extensible modular monolith  
**Initial rollout:** One organization, multiple sites; organization-scoped model prepared for future multi-organization support

> **Design principle:** OTARM records and evaluates OT assets. It must NEVER probe, scan, write to, configure, or patch production OT equipment in v1. All asset/firmware/lifecycle assertions come from human-provided evidence or validated imports, not inferred from a product name alone.

---

## 1. Product purpose

OTARM is a centralized, auditable web application for: (1) OT inventory and ownership, (2) firmware/OS and support-lifecycle monitoring, (3) structured assessments and findings, (4) transparent risk scoring and prioritization, (5) assigned remediation and acceptance workflows, and (6) executive and engineering dashboards. Intended environments include industrial manufacturing, power and water/wastewater plants.

### Primary personas
- **OT Assessor:** registers assets, validates records, performs assessments, creates findings, follows up corrective actions.
- **Remediation Owner:** responsible for implementing treatment plans and submitting proof of completion; an Assessor/Approver account may also be assigned remediation ownership.
- **Risk Approver:** verifies closure or formally accepts risk with rationale, review date, and safeguards.
- **Plant/OT Manager:** reviews risk exposure and overdue actions.
- **Organization Admin:** manages memberships, sites and configuration; no implicit bypass of separation-of-duties rules.

### Success definition for production MVP
A team can upload a fictional 30+ asset dataset, complete assessments, triage findings, assign remediation, verify/accept a finding, export prioritized work, and view a dashboard that updates from persisted records—without connecting to any OT hardware.

## 2. Product boundaries

### In scope for v1
1. Authentication, session management, organization membership, roles.
2. Site → area → control-system hierarchy within an organization.
3. Asset registration, detail edit, archive, search, filters, network/software details.
4. Product support/lifecycle evidence, review dates and attention flags.
5. Versioned assessment template with structured answers and free-text evidence.
6. Assessment findings; one asset may have many findings.
7. Deterministic initial candidate-finding rules, requiring human confirmation.
8. Impact × likelihood scoring, initial and residual rating; documented overrides.
9. Remediation actions, owners, due dates, verification, risk acceptance.
10. Dashboard KPIs, filters, priority list and CSV exports.
11. Validated CSV import with preview, error reporting and atomic commit.
12. Append-only business audit trail and seed/demo data.

### Out of scope v1
Network scanning (active OR passive), protocol polling (SNMP/Modbus/OPC UA/etc.), live vulnerability/CVE matching, automatic firmware classification by model, CMDB integration, live SIEM/SCADA connectors, topology rendering, notification email, file attachments, automation of change-control tasks, SSO, AI recommendations, and a public SaaS multi-tenant billing/admin portal. Database structure may anticipate these but no incomplete UI stubs.

## 3. Functional requirements (IDs are binding)

| ID | Priority | Requirement | Testable behavior |
|---|---|---|---|
| FR-01 | P0 | Authenticate named user | Unauthenticated users cannot see application routes/data; login/logout persist session appropriately. |
| FR-02 | P0 | Enforce organization scope and RBAC server-side | Every read/write checks membership and role; foreign organization IDs yield a non-disclosing 404/403. |
| FR-03 | P0 | Configure site hierarchy | Org Admin creates sites/areas/systems; assets reference valid scoped parent entities. |
| FR-04 | P0 | Register asset | Required: organization, site, unique asset tag within org, type, display name, operational status, data verification state. |
| FR-05 | P0 | Asset details | Store vendor, model, serial, IP/interface records, OS/firmware, network zone, criticality, ownership, source and last verification date. |
| FR-06 | P0 | Inventory usability | Server-side paging, search, filters by site/type/criticality/lifecycle, safe sort, archive (no destructive delete). |
| FR-07 | P0 | Lifecycle evidence | Support state Unknown/Supported/Limited/End-of-Support/End-of-Life and independent verification source/date. No support-state inference. |
| FR-08 | P0 | Assess an asset | Create Draft; save answers; validate completeness; finalize immutable assessment snapshot with template version and assessor. |
| FR-09 | P0 | Suggested findings | Trigger deterministic candidate findings from confirmed answers; display reasoning; user confirms/dismisses with rationale. |
| FR-10 | P0 | Risk findings | Capture risk statement, scenario, impact 1–5, likelihood 1–5, controls, evidence, proposed action and status. |
| FR-11 | P0 | Risk arithmetic | Score=impact×likelihood; thresholds Low 1–5; Medium 6–11; High 12–19; Critical 20–25. |
| FR-12 | P0 | Remediation actions | Multiple actions may attach to finding; assignee, due date, planned treatment, workflow and evidence notes. |
| FR-13 | P0 | Verify treatment | Assignee cannot self-verify; independent approver records verification; residual risk recalculated only from verified assessment. |
| FR-14 | P0 | Risk acceptance | Approver records justification, expiry/review date, accountable owner, compensating controls, accepts without falsely marking mitigated. |
| FR-15 | P0 | Dashboard | Total active assets, assessed coverage, open findings by severity, unresolved lifecycle status, overdue actions, top priorities. |
| FR-16 | P0 | CSV ingestion | Preview row errors/warnings; reject invalid/duplicate tags and references; atomic import; generate import audit event. |
| FR-17 | P0 | Export | Authenticated authorized filtered asset, risk and remediation exports with safe CSV handling. |
| FR-18 | P0 | Audit log | Immutable who/when/operation/object/outcome record for asset, assessment, finding, treatment, acceptance, authentication events. |
| FR-19 | P1 | Dashboard filtering | All main widgets honor site and date/as-of filters when applicable; drilldowns use same filter set. |
| FR-20 | P1 | Risk trend | Store evaluation history so month-over-month changes do not overwrite historical decisions. |
| FR-21 | P1 | Mass edits | Future, after review and explicit design (not initial implementation). |

**Priority terms:** P0 = launch gate; P1 = improvement after all P0 quality gates are met.

## 4. Data model

### Core entity relationship map
```
Organization 1--* Membership *--1 User
Organization 1--* Site 1--* Area 1--* ControlSystem
Organization 1--* Asset *--1 Site
Asset *--0..1 Area; Asset *--0..1 ControlSystem
Asset 1--* NetworkInterface
Asset 1--* SoftwareComponent
Asset 1--* LifecycleRecord
Asset 1--* Assessment 1--* AssessmentAnswer
Assessment *--1 AssessmentTemplate (versioned)
Asset 1--* Finding 1--* RiskEvaluation
Finding 1--* RemediationAction
Finding 1--* RiskAcceptance (historical, at most one active)
Organization 1--* AuditEvent
```

**Common column convention:** All major entities use UUID `id` and `created_at`, `updated_at` UTC timestamps. Records storing business ownership include `organization_id` explicitly. Admin actions are still organization-scoped. Disable hard deletes of operational records; use `archived_at` where applicable.

### Entity definitions

**organizations**
- `id uuid PK`, `name varchar(160)`, `slug varchar(64) UNIQUE`, `created_at timestamptz`

**users**
- `id uuid PK`, `email citext UNIQUE`, `display_name varchar(160)`, auth-provider user fields. Credentials handled only through vetted auth integration; never bespoke password storage.

**memberships**
- `id uuid PK`, `organization_id FK`, `user_id FK`, `role enum ADMIN|ASSESSOR|APPROVER|VIEWER`, `is_active bool`, UNIQUE `(organization_id,user_id)`.
- A user may have membership in multiple organizations in future, but the MVP UI initializes one organization. Server resolves selected org from trusted session/membership, never from an unverified client parameter alone.

**sites**
- `id`, `organization_id FK`, `site_code varchar(32)`, `name varchar(160)`, `description`, `timezone IANA string`; UNIQUE `(organization_id,site_code)`.

**areas**
- `id`, `organization_id FK`, `site_id FK`, `area_code`, `name`; UNIQUE `(site_id,area_code)`.

**control_systems**
- `id`, `organization_id FK`, `site_id FK`, `area_id FK NULL`, `name`, `system_type enum PLC|DCS|SCADA|OTHER`, `description`.

**assets**
- `id`, `organization_id FK`, `site_id FK`, `area_id FK NULL`, `control_system_id FK NULL`, `asset_tag varchar(80)`, `name varchar(160)`, `type enum PLC|DCS_SERVER|SCADA_SERVER|ENGINEERING_WORKSTATION|HMI|NETWORK_SWITCH|FIREWALL|ROUTER|HISTORIAN|GATEWAY|OTHER`, `vendor`, `model`, `serial_number NULL`, `operational_status enum ACTIVE|STANDBY|OUT_OF_SERVICE|RETIRED`, `criticality enum LOW|MEDIUM|HIGH|SAFETY_CRITICAL`, `owner_user_id NULL`, `description`, `source_type enum MANUAL|CSV_IMPORT`, `last_verified_at NULL`, `verification_state enum VERIFIED|UNVERIFIED|STALE`, `archived_at NULL`, `created_by FK`.
- UNIQUE `(organization_id,asset_tag)`; avoid IP uniqueness: identical addresses can exist across isolated OT networks and sites.
- Validate site/area/system all belong to same organization and hierarchy.

**network_interfaces**
- `id`, `organization_id FK`, `asset_id FK`, `name`, `ip_address varchar(45) NULL`, `subnet_prefix smallint NULL`, `mac_address NULL`, `vlan_id integer NULL`, `zone_label NULL`, `network_access enum ISOLATED|OT_ONLY|IT_CONNECTED|EXTERNAL_REMOTE|UNKNOWN`, `notes`.
- Allow multiple per asset. Validate IP/CIDR format; `vlan_id` 1..4094 if present. Never use saved addresses to initiate traffic.

**software_components**
- `id`, `organization_id FK`, `asset_id FK`, `kind enum FIRMWARE|OPERATING_SYSTEM|APPLICATION|OTHER`, `name`, `version_string`, `vendor NULL`, `installed_at NULL`, `last_verified_at NULL`, `verification_source NULL`.
- Preserve vendor version strings (do not compare them lexically or as simple decimals).

**lifecycle_records**
- `id`, `organization_id FK`, `asset_id FK`, `component_id NULL FK`, `support_state enum UNKNOWN|SUPPORTED|LIMITED_SUPPORT|END_OF_SUPPORT|END_OF_LIFE`, `end_of_support_date NULL`, `end_of_life_date NULL`, `source_url NULL`, `source_note NULL`, `verified_at NULL`, `verified_by NULL`, `is_current bool`.
- History retained; one current lifecycle record per `(asset_id, component_id)` (use DB constraint/index appropriate to NULL semantics). Missing vendor evidence remains `UNKNOWN`.

**assessment_templates**
- `id`, `organization_id NULL` (null=system template), `key`, `version integer`, `title`, `status enum DRAFT|PUBLISHED|RETIRED`, `schema_json jsonb`, immutable after first use; UNIQUE `(organization_id,key,version)` with correct null handling.

**assessments**
- `id`, `organization_id FK`, `asset_id FK`, `template_id FK`, `assessor_user_id FK`, `status enum DRAFT|FINALIZED`, `started_at`, `finalized_at NULL`, `summary`, `snapshot_json jsonb NULL`.
- Once finalized, answers and snapshot cannot be edited; subsequent reassessment creates a new record. Do not auto-close earlier findings.

**assessment_answers**
- `id`, `organization_id FK`, `assessment_id FK`, `question_key`, `answer enum YES|NO|UNKNOWN|NOT_APPLICABLE`, `evidence_notes`, `evidence_source NULL`, `assessed_at`; UNIQUE `(assessment_id,question_key)`.
- For each template question, define whether YES or NO represents adequate control; UNKNOWN is never automatically adequate. N/A requires rationale where applicable.

**findings**
- `id`, `organization_id FK`, `asset_id FK`, `source_assessment_id NULL FK`, `finding_key varchar(80)`, `title`, `risk_scenario`, `control_gap`, `recommended_treatment`, `status enum OPEN|TREATMENT_IN_PROGRESS|MITIGATED|ACCEPTED`, `is_candidate bool`, `evidence_notes NULL`, `raised_by FK`, `raised_at`, `resolved_at NULL`.
- Multiple findings per asset; active candidate dedup scoped by asset + finding key; manual findings allowed. Candidate state must be confirmed by human to enter dashboard open risk counts.

**risk_evaluations**
- `id`, `organization_id FK`, `finding_id FK`, `evaluation_type enum INITIAL|REASSESSMENT|RESIDUAL`, `impact smallint`, `likelihood smallint`, `score smallint STORED`, `severity enum LOW|MEDIUM|HIGH|CRITICAL`, `rationale`, `evaluated_by FK`, `evaluated_at`, `is_current bool`, `scoring_policy_version`.
- CHECK impact, likelihood 1..5; `score = impact*likelihood` computed in a single domain service or database-generated method (never trust submitted score). History is immutable; one current evaluation per finding. All metrics use current risk score for open/treated findings and current residual for mitigated findings.

**remediation_actions**
- `id`, `organization_id FK`, `finding_id FK`, `title`, `description`, `assigned_to FK`, `due_date date`, `status enum OPEN|PLANNED|IN_PROGRESS|PENDING_VERIFICATION|VERIFIED|CANCELLED`, `completion_notes NULL`, `submitted_at NULL`, `verified_by FK NULL`, `verified_at NULL`, `verification_notes NULL`, `created_by FK`.
- A finding can have multiple actions. Cancel requires reason. `PENDING_VERIFICATION → VERIFIED` only by eligible Approver other than assignee.

**risk_acceptances**
- `id`, `organization_id FK`, `finding_id FK`, `accepted_by FK`, `accountable_owner_id FK`, `reason`, `compensating_controls`, `review_due_on date`, `status enum ACTIVE|EXPIRED|REVOKED`, `accepted_at`, `revoked_at NULL`.
- Formal acceptance does not imply remediation, and should appear distinctly on reports; reject self-approval by assessor/action owner. Cron/periodic job for expiry is a later feature; in v1 compute expiry on reads from `review_due_on` and require reassessment when overdue.

**audit_events**
- `id`, `organization_id FK`, `actor_user_id FK NULL`, `occurred_at timestamptz`, `action enum`, `entity_type`, `entity_id`, `result enum SUCCESS|DENIED|FAILURE`, `change_summary_json jsonb`, `request_id`.
- Append-only via application permissions. Never log secrets, session tokens, or password material. Restrict read to admin/approver and protect archival backups.

### Essential indexes
- Assets: `(organization_id,site_id,type,archived_at)`, `(organization_id,asset_tag) UNIQUE`, search supporting `name`, `model`.
- Findings: `(organization_id,status,raised_at)`, `(asset_id,status)`.
- Risk evaluations: `(finding_id,is_current)`, partial uniqueness for current evaluation.
- Remediation: `(organization_id,status,due_date)`, `(assigned_to,status)`.
- Audit: `(organization_id,occurred_at DESC)`, `(entity_type,entity_id,occurred_at)`.
- Every foreign-key pair involving `organization_id` must be validated to prevent cross-organization relation injection; preferably use composite scoped FKs or service-layer transactional validation plus integration tests.

## 5. Assessment content and risk rules

### Template OT-BASELINE v1 (15 questions)
| Key | Control question | Risk candidate if confirmed adverse | Notes |
|---|---|---|---|
| OT01 | Asset owner is assigned and current | Unassigned ownership | No unknown-to-safe conversion |
| OT02 | Current configuration/recovery backup is available | Recovery readiness gap | Source must be verified |
| OT03 | Backup restoration has been tested on an appropriate schedule | Untested recovery | Varies by asset |
| OT04 | Remote vendor access is approval-controlled, time-limited and logged | Excessive remote access | Controls and exceptions documented |
| OT05 | Asset network connectivity follows approved zone/conduit rules | Inadequate segmentation | Do not auto-infer from IP |
| OT06 | External/IT reachability is justified and documented | Excessive exposure | Assessor validates paths |
| OT07 | Accounts are individually attributable or formally managed | Shared/uncontrolled credentials | Never store passwords |
| OT08 | Least privilege is implemented where equipment supports it | Excessive privilege | Equipment feasibility considered |
| OT09 | Software/firmware versions are documented | Incomplete software inventory | Data-quality gap |
| OT10 | Vendor support/lifecycle is verified | Unsupported or unverified support | Only label EOL with evidence |
| OT11 | Security patch/change procedure respects process safety | No controlled patch process | Not a demand for automatic patching |
| OT12 | OT antivirus/allowlisting/approved compensating controls documented | Endpoint protection gap | May be N/A for PLC |
| OT13 | Firewall/remote access rule review is documented | Rule governance gap | May be N/A by asset type |
| OT14 | Recovery dependencies and redundancy are documented | Availability/redundancy gap | Distinguish acceptable single points |
| OT15 | Incident response/escalation owner and procedure are defined | Response readiness gap | Per relevant control-system context |

**Assessment answers:** YES = control present; NO = confirmed gap; UNKNOWN = insufficient evidence; NOT_APPLICABLE = justified exception. These semantic meanings apply to these positively worded questions. A NO creates a **candidate** finding with trace to question, answer and rationale; user decides confirm/dismiss. UNKNOWN creates a data-quality follow-up, never scores as 0 or creates an unsubstantiated vulnerability. Critical data-quality gaps are highlighted separately on dashboard. Don't create duplicate active findings for repeat assessments—offer link/update existing finding and capture additional evidence.

### Risk scoring policy OTARM-5X5 v1
- `impact` = 1 negligible; 2 minor local; 3 moderate downtime; 4 major production impact; 5 severe safety/production/mission consequence. Assessor must record which of safety, production, financial and regulatory factors determined impact; score uses highest credible consequence with narrative.
- `likelihood` = 1 rare; 2 unlikely; 3 possible; 4 likely; 5 very likely. Assessor justifies based on verified exposure, controls and credible scenarios; do not make numeric likelihood claims without data.
- `score=impact*likelihood`. Band definitions: 1–5 LOW; 6–11 MEDIUM; 12–19 HIGH; 20–25 CRITICAL. **Project-defined policy, not a numeric scale prescribed by NIST or IEC.**
- Dashboard open-risk metrics count confirmed, non-closed findings; accepted risks shown in own count; findings with no evaluation show `UNSCORED` and remain visible.
- **Prioritization algorithm:** sort open/unaccepted findings by severity band descending, score descending, safety-critical asset before others on ties, then past-due remediation before non-past-due, then oldest finding first; show plain-language explanation. Do not sum risk scores across assets and claim an organization probability.
- **Asset roll-up:** highest currently open confirmed finding severity per asset; `NO_OPEN_FINDINGS` if none, separately flag `NOT_ASSESSED` and lifecycle `UNKNOWN` so a blank record cannot be displayed as healthy.
- **Treatment:** store immutable INITIAL and later RESIDUAL evaluations; independent verification checks controls and assigns post-treatment impact/likelihood. Risk score doesn't automatically decrease when an action is marked done.

## 6. Workflows and state transitions

### WF-01 Register or import asset
`Create/Edit → Validate → Save → Audit → Display`. Required hierarchy scope check. Import uses `Upload → Parse → Dry-run preview/errors → User confirms → Single transaction commit → Summary & audit`. Reject malicious CSV formula strings when exporting (prefix dangerous leading characters or otherwise neutralize them). Row failures must not cause hidden partial imports.

### WF-02 Assess asset
`Open Asset → New Assessment (template version pinned) → Draft answers → Validate → Finalize immutable snapshot → Propose findings → Confirm/dismiss candidates → Score confirmed findings → Audit`. Unknown questions stay unknown and visible; complete finalization means questions are answered (including Unknown/N/A), not necessarily secure.

### WF-03 Remediate finding
`OPEN → TREATMENT_IN_PROGRESS → MITIGATED` only after all required actions are VERIFIED and independent risk evaluation completed. Actions: `OPEN → PLANNED → IN_PROGRESS → PENDING_VERIFICATION → VERIFIED`. Authorized actor may cancel with reason. Authorized reassessment can reopen a previously mitigated finding, retaining prior history.

### WF-04 Accept risk
`Open Finding → Request acceptance → Approver reviews context/controls → Approve with reason + accountable owner + review date → ACCEPTED`. Active acceptance expiry must be displayed as overdue and may require follow-up; acceptance is never counted as mitigated. Reject action-owner/assessor self-approval. Admin cannot silently bypass; if single-user instance has no independent approver, acceptance action stays unavailable.

### WF-05 Lifecycle review
`Update component/version → Check trusted vendor documentation manually → Record source + review date → Set support state → Review flag generation`. Changing version must not silently mark previous vendor support evidence as verified for new version.

## 7. Screens / UX contract

| Page / route | Required controls / information |
|---|---|
| `/login` | Secure sign-in/error/logout, no public data |
| `/dashboard` | Site filter, KPI cards, severity chart, asset/assessment coverage, top 10 priorities, lifecycle unknown/EOL summary, overdue actions; every count clickable |
| `/assets` | Paginated table: tag/name/type/site/criticality/lifecycle/highest open finding, filter, search, import, export, create |
| `/assets/new` | Required asset form with valid site/area/control-system cascade |
| `/assets/[id]` | Header+status; tabs Overview / Network & Software / Lifecycle / Assessments / Findings / Activity; create assessment, add manual finding, edit/archive |
| `/assessments/[id]` | Template version, answers YES/NO/UNKNOWN/N/A, notes, progress, draft/save/finalize, resulting candidate findings |
| `/findings` | Status/severity/site filters, priority sorted listing, findings without score/with unknown evidence visible |
| `/findings/[id]` | Scenario, controls, rating and rationale history, evidence, actions, acceptance, approval trail |
| `/remediation` | Action table, owner, due date, status; create/update/submit for verification |
| `/reports` | Filtered export of assets, findings, treatment actions and printable view (full PDF report deferred) |
| `/settings/sites` | Admin CRUD for sites, areas, control systems |
| `/settings/users` | Admin manage organization memberships and roles |
| `/settings/audit` | Filterable audit events accessible only to admin/approver |

UX requirements: desktop-first, usable at 1280px width; tablet responsive; no dead-end links. Blank states prompt sensible next action. Clearly label DEMO datasets, UNKNOWN evidence, accepted vs mitigated risk, and all non-verified calculated indicators. All tables support empty/loading/error conditions.

## 8. Permission matrix

| Function | Admin | Assessor | Approver | Viewer |
|---|:---:|:---:|:---:|:---:|
| View organization data | Yes | Yes | Yes | Yes |
| Manage sites and membership | Yes | No | No | No |
| Add/edit/archive assets | Yes | Yes | No | No |
| Create/finalize assessment | Yes | Yes | No | No |
| Create/score findings | Yes | Yes | No | No |
| Create/submit own assigned remediation | Yes | Yes | Yes | No |
| Verify submitted action | If independent | No | If independent | No |
| Accept risk | If independent | No | If independent | No |
| Export organization data | Yes | Yes | Yes | No |
| View audit trail | Yes | No | Yes | No |

`If independent` = actor is not the assessor/assignee directly involved in the decision. Enforce checks in service layer and API on every request, not via hidden UI buttons.

## 9. Dashboard rules

- **Total active inventory:** count assets where `archived_at IS NULL` and `operational_status != RETIRED`.
- **Assessed coverage:** distinct active assets with ≥1 finalized assessment / total active assets. Report `0/0 = N/A`, not 100%. Provide separate recently assessed (`finalized_at` within configurable policy, default 365 days) indicator.
- **Open risk by severity:** counts only confirmed unaccepted, unmitigated findings with current risk evaluation. Unscored shown separately.
- **Lifecycle unresolved:** count active assets with current support state UNKNOWN, unsupported/ended states or missing verification; groups can overlap; present them transparently.
- **Overdue actions:** actions where due_date < organization's current business date and status not VERIFIED or CANCELLED.
- **Priority list:** deterministic policy in §5; drill through to findings. Do not claim zero risk based on zero findings when inventory is unassessed.
- **Accepted risks:** separately show active and expired acceptance. Never mix into `mitigated`.
- **Historical as-of metrics:** v1 current-state; full event-sourced historical trending P1 unless a persisted periodic snapshot is implemented.

## 10. APIs (contract sketch)

Implement authenticated versioned internal routes (JSON for CRUD; CSV for exports). Use schema validation and pagination, typed errors, standard `201/200/400/401/403/404/409` semantics. All IDs are UUIDs.

```
GET    /api/v1/dashboard/summary?siteId=
GET    /api/v1/sites
POST   /api/v1/sites
GET    /api/v1/assets?page=&pageSize=&siteId=&type=&search=
POST   /api/v1/assets
GET    /api/v1/assets/:id
PATCH  /api/v1/assets/:id
POST   /api/v1/assets/:id/archive
POST   /api/v1/assets/import/preview
POST   /api/v1/assets/import/commit
GET    /api/v1/assets/export
POST   /api/v1/assets/:id/assessments
GET    /api/v1/assessments/:id
PATCH  /api/v1/assessments/:id/answers
POST   /api/v1/assessments/:id/finalize
POST   /api/v1/assessments/:id/candidates/:candidateKey/confirm
POST   /api/v1/assessments/:id/candidates/:candidateKey/dismiss
GET    /api/v1/findings?siteId=&status=&severity=
GET    /api/v1/findings/:id
POST   /api/v1/findings
POST   /api/v1/findings/:id/evaluations
POST   /api/v1/findings/:id/actions
PATCH  /api/v1/actions/:id
POST   /api/v1/actions/:id/submit-verification
POST   /api/v1/actions/:id/verify
POST   /api/v1/findings/:id/acceptances
GET    /api/v1/remediation
GET    /api/v1/audit-events
GET    /api/v1/exports/findings.csv
GET    /api/v1/exports/remediation.csv
```

Do not expose user-controlled generic SQL or internal data dumps. Rate-limit authentication and import endpoints. Mutations should be transactional with event logging; commit stage should reference server-maintained preview/import token bound to organization and user, not trust arbitrary raw client rows.

## 11. Nonfunctional requirements

| ID | Requirement |
|---|---|
| NFR-01 Security | HTTPS only on deployed system; session cookies HttpOnly/Secure/SameSite; CSRF strategy matched to auth; input validation; output encoding; security headers; no public OT inventory pages. |
| NFR-02 Authorization | Deny by default; org-scoped server-side checks for ALL endpoints; tests against IDOR and horizontal privilege escalation. |
| NFR-03 Authentication | Vetted auth library with MFA via supported provider for production deployment; no default admin/demo credentials on production. |
| NFR-04 Data integrity | Migrations under version control, DB constraints, serializable/transaction-safe import and approval updates, no silent partial writes. |
| NFR-05 Availability | Define deployment target 99.5% availability (operational objective, not guaranteed) and document backup/recovery. |
| NFR-06 Performance | Reference dataset: 10,000 assets, 50,000 findings across sites; paginated inventory P95 API < 1 second, dashboard P95 < 2 seconds under stated test hardware/load; measure, don't guarantee untested. |
| NFR-07 Security logging | Authentication outcomes, failed authorization, all business changes, acceptance and verification; UTC times, actor, entity, request ID. |
| NFR-08 Backups | Automated encrypted PostgreSQL backups, daily minimum, 30-day suggested retention; tested restore before production. Set actual RPO/RTO in operations runbook. |
| NFR-09 Data handling | Classify IPs, network zones and asset inventory as sensitive; secrets never entered in asset fields; backups encrypted and access-controlled. |
| NFR-10 Deployment | Dockerized, reproducible migrations/seeding; health check, documented reverse-proxy TLS and restore procedure. |
| NFR-11 Maintainability | Strict TS, lint/format checks, domain services, API contracts, schema migration tests, CI; pin/lock dependency versions. |
| NFR-12 Usability | Visible errors, accessible field labels, WCAG 2.2 AA aspiration, keyboard navigation, desktop/tablet responsive. |

**Deployment position:** For real plant data, host behind corporate VPN/ZTNA or restricted application gateway; avoid publicly indexed/open internet access. Never put app server on OT control network by default. Use a sanctioned IT network placement and data flow review.

## 12. Acceptance criteria — release gates

**AC-01** Unauthenticated GET to `/dashboard` and all sensitive APIs receives no OT data.  
**AC-02** Viewer cannot write assets/actions; permitted write attempts receive 403.  
**AC-03** A member of Org A cannot read Org B asset ID via any page, API or export; test cross-org FK tampering on every entity type.  
**AC-04** User can create 30 diverse assets and see them after app/database restart.  
**AC-05** Duplicate asset tag within organization is rejected with helpful message; same IP at different isolated sites is allowed.  
**AC-06** Changing firmware/software version does not silently preserve vendor support verification for the new version.  
**AC-07** CSV preview reports exact row numbers and errors; failed commit imports zero rows.  
**AC-08** A 15-question assessment saves Draft, finalizes, and can no longer be silently edited; a later assessment creates a new version.  
**AC-09** NO answer suggests an explainable candidate finding, requiring explicit confirmation; UNKNOWN is never displayed as compliant.  
**AC-10** Confirmed finding with impact=5 and likelihood=4 yields 20, CRITICAL; boundary tests 5/6/11/12/19/20/25 pass.  
**AC-11** One asset can hold 3 separate findings with independent histories and actions.  
**AC-12** Completing an action alone does not close the finding or reduce risk score; independent verification + residual assessment required.  
**AC-13** Same person cannot verify their own action or accept their own assessed risk; server denies even if UI altered.  
**AC-14** Accepted risk retains rationale, owner, expiry; appears as accepted, not mitigated; expired acceptance flagged.  
**AC-15** Dashboard totals match filtered database rows; coverage distinguishes no findings from not assessed.  
**AC-16** Export honors organization and filters; cells beginning `=`, `+`, `-`, `@` cannot execute as spreadsheet formulas.  
**AC-17** Asset edit, assessment finalize, finding score, action verification and acceptance generate append-only audit entries.  
**AC-18** Test suite (unit + integration + e2e), lint, type-check, migration on fresh DB and Docker smoke test pass before release.  
**AC-19** Application never sends requests to stored device IPs or executes OT protocol discovery code.  
**AC-20** No hardcoded auth secrets, demo passwords or sensitive production plant data shipped in repository.

## 13. Quality/testing matrix

- **Unit:** risk arithmetic/severity/boundaries; priority deterministic tie-breaks; assessment candidate generation; asset lifecycle status; CSV validation/sanitization.
- **Integration:** scoped FK validation, transactions, concurrent duplicate asset creation, import atomicity, immutable assessment, state machine, approval separation.
- **End-to-end:** login → create asset → assessment → confirm risk → create treatment → submit verification → independent approver verifies → residual assessment → dashboard/export.
- **Security:** horizontal IDOR, privilege escalation, CSRF, auth/session invalidation, XSS in notes, injection attempts, CSV injection, upload limits and error handling.
- **Performance:** 10k/50k synthetic workload, index/explain review, paginated list and dashboard p95.

## 14. Deployment and repository deliverables

```
otarm/
  app/                       # Next.js routes and UI
  components/                # Shared views and field components
  modules/
    assets/                  # schemas, service, repository, tests
    lifecycle/
    assessments/
    risks/
    remediation/
    dashboard/
    audit/
  lib/auth/                   # auth + authorization guards
  lib/db/                     # Prisma/database client
  prisma/schema.prisma
  prisma/migrations/
  prisma/seed.ts              # clearly fake DEMO data only
  tests/integration/
  tests/e2e/
  docs/ARCHITECTURE.md
  docs/SECURITY.md
  docs/RISK_SCORING.md
  docs/OPERATIONS.md
  .env.example
  docker-compose.yml
  Dockerfile
  README.md
```

CI must run typecheck, lint, unit/integration tests, migration build, E2E smoke on seeded nonproduction database. Keep `.env`, credentials, database dumps and private asset inventories outside Git.

## 15. Deliverables / milestones

1. **Foundation:** authenticated skeleton, Postgres/Prisma, user/role/org/site data isolation.
2. **Inventory:** hierarchy CRUD, asset/network/software/lifecycle, CSV dry-run and exports.
3. **Assessment:** published template, draft/finalize/versioning, candidates, manual findings.
4. **Risk engine:** scoring, history, priority register and aggregate logic.
5. **Treatment:** actions, independent verification, residual evaluation, acceptance and audit.
6. **Dashboards/reports:** filters, metrics, summaries and traceable drilldown.
7. **Hardening/release:** CI, security tests, load/restore tests, Docker deployment and docs.

See accompanying `OTARM_Codex_Implementation_Plan_v1.md` for actionable prompts and finish gates.

## 16. Reference baseline (for design, not a certificate of compliance)

- NIST SP 800-82 Rev. 3 (Sept. 2023, final) — https://csrc.nist.gov/pubs/sp/800/82/r3/final ; Sept. 2026 initial public draft of Rev. 4 is not final as of 2026-10-17.
- NIST CSF 2.0 — https://www.nist.gov/cyberframework
- OWASP ASVS 5.0 — https://owasp.org/projects/asvs
- IEC 62443 concept alignment (zones, conduits and risk assessment); do not assert formal IEC 62443 compliance based only on this application.

## 17. Scope change control

Any new feature requires: proposed user value, security impact, data migration impact, dependencies, acceptance criteria, and phase assignment. Refuse speculative integrations until all P0 launch gates pass. If upstream library APIs have evolved, Codex should verify compatibility with pinned/current stable versions and document deviations rather than improvising architecture changes.
