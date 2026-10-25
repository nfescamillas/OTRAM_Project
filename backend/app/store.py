from __future__ import annotations

import csv
import io
import secrets
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Engine, func, or_, select
from sqlalchemy.exc import IntegrityError

from .database import Base, create_database_engine, create_session_factory
from .entities import AssetEntity, AuditEventEntity, FindingEntity, RemediationActionEntity, SiteEntity, UserEntity
from .models import (
    ActionStatus, Asset, AssetInput, AssetType, AuditEvent, AuditResult, Criticality,
    DashboardSummary, Finding, FindingStatus, LifecycleState, OperationalStatus,
    RemediationAction, Role, Severity, SeverityCounts, Site, UserRecord, VerificationState,
)
from .seed import seed_database
from .telemetry import ApplicationMetrics


class StoreError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class DatabaseStore:
    """SQLAlchemy-backed repository with organization-scoped queries."""

    def __init__(self, database_url: str, demo_password: str | None = None, *,
                 password_iterations: int = 310_000, engine: Engine | None = None,
                 sync_demo_password: bool = False) -> None:
        self.engine = engine or create_database_engine(database_url)
        self.metrics: ApplicationMetrics | None = None
        self._sessions = create_session_factory(self.engine)
        Base.metadata.create_all(self.engine)
        with self._sessions() as session:
            seed_database(session, demo_password or secrets.token_urlsafe(24), password_iterations,
                          sync_demo_password=sync_demo_password)

    def dispose(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _user(row: UserEntity) -> UserRecord:
        return UserRecord(id=row.id, email=row.email, displayName=row.display_name, role=Role(row.role),
                          organizationId=row.organization_id, passwordHash=row.password_hash)

    @staticmethod
    def _site(row: SiteEntity) -> Site:
        return Site(id=row.id, code=row.code, name=row.name)

    @staticmethod
    def _asset(row: AssetEntity) -> Asset:
        return Asset(id=row.id, tag=row.tag, name=row.name, type=AssetType(row.type), siteId=row.site_id,
                     area=row.area, vendor=row.vendor, model=row.model, criticality=Criticality(row.criticality),
                     lifecycle=LifecycleState(row.lifecycle), verification=VerificationState(row.verification),
                     lastVerifiedAt=row.last_verified_at, operationalStatus=OperationalStatus(row.operational_status),
                     owner=row.owner, firmware=row.firmware, networkZone=row.network_zone,
                     ipAddress=row.ip_address, assessed=row.assessed)

    @staticmethod
    def _finding(row: FindingEntity) -> Finding:
        return Finding(id=row.id, assetId=row.asset_id, title=row.title, riskScenario=row.risk_scenario,
                       controlGap=row.control_gap, recommendedTreatment=row.recommended_treatment,
                       status=FindingStatus(row.status), impact=row.impact, likelihood=row.likelihood,
                       severity=Severity(row.severity), score=row.score, raisedAt=row.raised_at,
                       dueDate=row.due_date, owner=row.owner)

    @staticmethod
    def _action(row: RemediationActionEntity) -> RemediationAction:
        return RemediationAction(id=row.id, findingId=row.finding_id, title=row.title,
                                 assignedTo=row.assigned_to, dueDate=row.due_date,
                                 status=ActionStatus(row.status), completionNotes=row.completion_notes)

    @staticmethod
    def _audit(row: AuditEventEntity) -> AuditEvent:
        occurred = row.occurred_at
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
        return AuditEvent(id=row.id, actor=row.actor, action=row.action, entity=row.entity,
                          occurredAt=occurred, result=AuditResult(row.result))

    def user_by_email(self, email: str) -> UserRecord | None:
        with self._sessions() as session:
            row = session.scalar(select(UserEntity).where(func.lower(UserEntity.email) == email.strip().lower()))
            return self._user(row) if row else None

    def user_by_id(self, user_id: str) -> UserRecord | None:
        with self._sessions() as session:
            row = session.get(UserEntity, user_id)
            return self._user(row) if row else None

    def list_sites(self, user: UserRecord) -> list[Site]:
        with self._sessions() as session:
            rows = session.scalars(select(SiteEntity).where(SiteEntity.organization_id == user.organizationId).order_by(SiteEntity.name)).all()
            return [self._site(row) for row in rows]

    def list_assets(self, user: UserRecord, *, search: str | None = None, site_id: str | None = None,
                    asset_type: AssetType | None = None, lifecycle: LifecycleState | None = None) -> list[Asset]:
        statement = select(AssetEntity).where(AssetEntity.organization_id == user.organizationId)
        if site_id:
            statement = statement.where(AssetEntity.site_id == site_id)
        if asset_type:
            statement = statement.where(AssetEntity.type == asset_type.value)
        if lifecycle:
            statement = statement.where(AssetEntity.lifecycle == lifecycle.value)
        query = (search or "").strip().lower()
        if query:
            match = f"%{query}%"
            statement = statement.where(or_(func.lower(AssetEntity.tag).like(match),
                                             func.lower(AssetEntity.name).like(match),
                                             func.lower(AssetEntity.vendor).like(match),
                                             func.lower(AssetEntity.model).like(match)))
        with self._sessions() as session:
            return [self._asset(row) for row in session.scalars(statement.order_by(AssetEntity.id)).all()]

    def get_asset(self, user: UserRecord, asset_id: str) -> Asset:
        with self._sessions() as session:
            row = session.scalar(select(AssetEntity).where(AssetEntity.id == asset_id,
                                                            AssetEntity.organization_id == user.organizationId))
            if row is None:
                raise StoreError(404, "NOT_FOUND", "The requested asset was not found.")
            return self._asset(row)

    def create_asset(self, user: UserRecord, data: AssetInput) -> Asset:
        with self._sessions.begin() as session:
            site_exists = session.scalar(select(SiteEntity.id).where(SiteEntity.id == data.siteId,
                                                                      SiteEntity.organization_id == user.organizationId))
            if not site_exists:
                raise StoreError(400, "VALIDATION", "The selected site is invalid.")
            duplicate = session.scalar(select(AssetEntity.id).where(AssetEntity.organization_id == user.organizationId,
                                                                     func.lower(AssetEntity.tag) == data.tag.casefold()))
            if duplicate:
                raise StoreError(409, "CONFLICT", "Asset tag already exists.")
            row = AssetEntity(id=f"a-{uuid4()}", organization_id=user.organizationId,
                              site_id=data.siteId, tag=data.tag, name=data.name, type=data.type.value,
                              area=data.area, vendor=data.vendor, model=data.model,
                              criticality=data.criticality.value, lifecycle=data.lifecycle.value,
                              verification=data.verification.value, last_verified_at=data.lastVerifiedAt,
                              operational_status=data.operationalStatus.value, owner=data.owner,
                              firmware=data.firmware, network_zone=data.networkZone,
                              ip_address=data.ipAddress, assessed=data.assessed)
            session.add(row)
            self._append_audit(session, user, "ASSET_CREATED", row.tag)
            try:
                session.flush()
            except IntegrityError as exc:
                raise StoreError(409, "CONFLICT", "Asset tag already exists.") from exc
            if data.assessed and self.metrics is not None:
                self.metrics.risk_assessments.add(1, {"status": "completed"})
            return self._asset(row)

    def list_findings(self, user: UserRecord, *, site_id: str | None = None,
                      status: FindingStatus | None = None, severity: Severity | None = None) -> list[Finding]:
        statement = (select(FindingEntity).join(AssetEntity, FindingEntity.asset_id == AssetEntity.id)
                     .where(FindingEntity.organization_id == user.organizationId,
                            AssetEntity.organization_id == user.organizationId))
        if site_id:
            statement = statement.where(AssetEntity.site_id == site_id)
        if status:
            statement = statement.where(FindingEntity.status == status.value)
        if severity:
            statement = statement.where(FindingEntity.severity == severity.value)
        with self._sessions() as session:
            return [self._finding(row) for row in session.scalars(statement.order_by(FindingEntity.id)).all()]

    def list_actions(self, user: UserRecord) -> list[RemediationAction]:
        with self._sessions() as session:
            rows = session.scalars(select(RemediationActionEntity).where(
                RemediationActionEntity.organization_id == user.organizationId).order_by(RemediationActionEntity.id)).all()
            return [self._action(row) for row in rows]

    def update_action(self, user: UserRecord, action_id: str, status: ActionStatus) -> RemediationAction:
        with self._sessions.begin() as session:
            row = session.scalar(select(RemediationActionEntity).where(
                RemediationActionEntity.id == action_id,
                RemediationActionEntity.organization_id == user.organizationId))
            if row is None:
                raise StoreError(404, "NOT_FOUND", "The requested remediation action was not found.")
            current = ActionStatus(row.status)
            allowed = {
                ActionStatus.OPEN: {ActionStatus.PLANNED, ActionStatus.CANCELLED},
                ActionStatus.PLANNED: {ActionStatus.IN_PROGRESS, ActionStatus.CANCELLED},
                ActionStatus.IN_PROGRESS: {ActionStatus.PENDING_VERIFICATION, ActionStatus.CANCELLED},
                ActionStatus.PENDING_VERIFICATION: {ActionStatus.VERIFIED, ActionStatus.IN_PROGRESS},
                ActionStatus.VERIFIED: set(), ActionStatus.CANCELLED: set(),
            }
            if status not in allowed[current]:
                raise StoreError(409, "CONFLICT", f"Cannot move action from {current} to {status}.")
            if status == ActionStatus.VERIFIED and user.role not in {Role.ADMIN, Role.APPROVER}:
                raise StoreError(403, "FORBIDDEN", "Only an independent approver may verify remediation.")
            if status == ActionStatus.VERIFIED and row.assigned_to.casefold() == user.displayName.casefold():
                raise StoreError(403, "FORBIDDEN", "An assignee cannot verify their own remediation action.")
            row.status = status.value
            self._append_audit(session, user, "ACTION_STATUS_CHANGED", row.title)
            session.flush()
            return self._action(row)

    def list_audit(self, user: UserRecord) -> list[AuditEvent]:
        with self._sessions() as session:
            rows = session.scalars(select(AuditEventEntity).where(
                AuditEventEntity.organization_id == user.organizationId).order_by(AuditEventEntity.occurred_at.desc())).all()
            return [self._audit(row) for row in rows]

    def dashboard(self, user: UserRecord, site_id: str | None = None) -> DashboardSummary:
        assets = [a for a in self.list_assets(user, site_id=site_id) if a.operationalStatus != OperationalStatus.RETIRED]
        asset_ids = {a.id for a in assets}
        findings = [f for f in self.list_findings(user, site_id=site_id) if f.assetId in asset_ids]
        actions = self.list_actions(user)
        open_findings = [f for f in findings if f.status in {FindingStatus.OPEN, FindingStatus.TREATMENT_IN_PROGRESS}]
        counts = SeverityCounts()
        for finding in open_findings:
            setattr(counts, finding.severity.value, getattr(counts, finding.severity.value) + 1)
        open_ids = {f.id for f in open_findings}
        today = date.today()
        overdue = sum(1 for action in actions if action.findingId in open_ids and action.dueDate < today
                      and action.status not in {ActionStatus.VERIFIED, ActionStatus.CANCELLED})
        assessed = sum(1 for asset in assets if asset.assessed)
        severity_rank = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}
        asset_by_id = {asset.id: asset for asset in assets}
        action_by_finding = {action.findingId: action for action in actions}

        def priority(finding: Finding):
            asset = asset_by_id[finding.assetId]
            action = action_by_finding.get(finding.id)
            safety = asset.criticality == Criticality.SAFETY_CRITICAL
            past_due = bool(action and action.dueDate < today and action.status not in {ActionStatus.VERIFIED, ActionStatus.CANCELLED})
            return (-severity_rank[finding.severity], -finding.score, -int(safety), -int(past_due), finding.raisedAt)

        return DashboardSummary(activeAssets=len(assets), assessedAssets=assessed,
            coveragePercent=int(assessed / len(assets) * 100 + 0.5) if assets else None,
            severityCounts=counts,
            lifecycleUnresolved=sum(1 for asset in assets if asset.lifecycle in {LifecycleState.UNKNOWN, LifecycleState.END_OF_SUPPORT, LifecycleState.END_OF_LIFE}),
            overdueActions=overdue, acceptedRisks=sum(1 for finding in findings if finding.status == FindingStatus.ACCEPTED),
            unscoredFindings=0, topPriorities=sorted(open_findings, key=priority)[:10])

    def export_assets(self, user: UserRecord, **filters) -> str:
        assets = self.list_assets(user, **filters)
        site_names = {site.id: site.name for site in self.list_sites(user)}
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["Asset tag", "Name", "Type", "Site", "Criticality", "Lifecycle", "Owner"])
        for asset in assets:
            row = [asset.tag, asset.name, asset.type.value, site_names[asset.siteId],
                   asset.criticality.value, asset.lifecycle.value, asset.owner or ""]
            writer.writerow([f"'{value}" if str(value).startswith(("=", "+", "-", "@")) else value for value in row])
        return output.getvalue()

    def _append_audit(self, session, user: UserRecord, action: str, entity: str) -> None:
        session.add(AuditEventEntity(id=f"e-{uuid4()}", organization_id=user.organizationId,
                                     actor=user.displayName, action=action, entity=entity,
                                     occurred_at=datetime.now(timezone.utc), result=AuditResult.SUCCESS.value))
        if self.metrics is not None:
            self.metrics.audit_events.add(1, {"event.type": action, "result": "success"})
