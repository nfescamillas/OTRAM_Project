from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Role(StrEnum):
    ADMIN = "ADMIN"
    ASSESSOR = "ASSESSOR"
    APPROVER = "APPROVER"
    VIEWER = "VIEWER"


class AssetType(StrEnum):
    PLC = "PLC"
    DCS_SERVER = "DCS_SERVER"
    SCADA_SERVER = "SCADA_SERVER"
    ENGINEERING_WORKSTATION = "ENGINEERING_WORKSTATION"
    HMI = "HMI"
    NETWORK_SWITCH = "NETWORK_SWITCH"
    FIREWALL = "FIREWALL"
    ROUTER = "ROUTER"
    HISTORIAN = "HISTORIAN"
    GATEWAY = "GATEWAY"
    OTHER = "OTHER"


class Criticality(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    SAFETY_CRITICAL = "SAFETY_CRITICAL"


class LifecycleState(StrEnum):
    UNKNOWN = "UNKNOWN"
    SUPPORTED = "SUPPORTED"
    LIMITED_SUPPORT = "LIMITED_SUPPORT"
    END_OF_SUPPORT = "END_OF_SUPPORT"
    END_OF_LIFE = "END_OF_LIFE"


class VerificationState(StrEnum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    STALE = "STALE"


class OperationalStatus(StrEnum):
    ACTIVE = "ACTIVE"
    STANDBY = "STANDBY"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    RETIRED = "RETIRED"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingStatus(StrEnum):
    OPEN = "OPEN"
    TREATMENT_IN_PROGRESS = "TREATMENT_IN_PROGRESS"
    MITIGATED = "MITIGATED"
    ACCEPTED = "ACCEPTED"


class ActionStatus(StrEnum):
    OPEN = "OPEN"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    CANCELLED = "CANCELLED"


class AuditResult(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"


class Site(StrictModel):
    id: str
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=160)


class AssetInput(StrictModel):
    tag: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    type: AssetType
    siteId: str
    area: str = Field(max_length=160)
    vendor: str = Field(max_length=160)
    model: str = Field(max_length=160)
    criticality: Criticality
    lifecycle: LifecycleState
    verification: VerificationState
    lastVerifiedAt: date | None = None
    operationalStatus: OperationalStatus
    owner: str | None = Field(default=None, max_length=160)
    firmware: str | None = Field(default=None, max_length=255)
    networkZone: str | None = Field(default=None, max_length=160)
    ipAddress: str | None = Field(default=None, max_length=45)
    assessed: bool = False


class Asset(AssetInput):
    id: str


class Finding(StrictModel):
    id: str
    assetId: str
    title: str
    riskScenario: str
    controlGap: str
    recommendedTreatment: str
    status: FindingStatus
    impact: int = Field(ge=1, le=5)
    likelihood: int = Field(ge=1, le=5)
    severity: Severity
    score: int = Field(ge=1, le=25)
    raisedAt: date
    dueDate: date | None = None
    owner: str | None = None


class RemediationAction(StrictModel):
    id: str
    findingId: str
    title: str
    assignedTo: str
    dueDate: date
    status: ActionStatus
    completionNotes: str | None = None


class UpdateActionStatusInput(StrictModel):
    status: ActionStatus


class AuditEvent(StrictModel):
    id: str
    actor: str
    action: str
    entity: str
    occurredAt: datetime
    result: AuditResult


class SeverityCounts(StrictModel):
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0


class DashboardSummary(StrictModel):
    activeAssets: int
    assessedAssets: int
    coveragePercent: int | None
    severityCounts: SeverityCounts
    lifecycleUnresolved: int
    overdueActions: int
    acceptedRisks: int
    unscoredFindings: int
    topPriorities: list[Finding]


class UserRecord(StrictModel):
    id: str
    email: str
    displayName: str
    role: Role
    organizationId: str
    passwordHash: str


class PublicUser(StrictModel):
    id: str
    email: str
    displayName: str
    role: Role


class LoginRequest(StrictModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(StrictModel):
    accessToken: str
    tokenType: str = "bearer"
    expiresIn: int
    user: PublicUser


class ApiError(StrictModel):
    code: str
    message: str
    requestId: str | None = None
    fields: dict[str, str] | None = None
