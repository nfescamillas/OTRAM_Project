from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class UserEntity(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(32))
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    password_hash: Mapped[str] = mapped_column(Text)


class SiteEntity(Base):
    __tablename__ = "sites"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(160))


class AssetEntity(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("organization_id", "tag", name="uq_asset_org_tag"),)
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    tag: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(String(64))
    area: Mapped[str] = mapped_column(String(160), default="")
    vendor: Mapped[str] = mapped_column(String(160), default="")
    model: Mapped[str] = mapped_column(String(160), default="")
    criticality: Mapped[str] = mapped_column(String(32))
    lifecycle: Mapped[str] = mapped_column(String(32))
    verification: Mapped[str] = mapped_column(String(32))
    last_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    operational_status: Mapped[str] = mapped_column(String(32))
    owner: Mapped[str | None] = mapped_column(String(160), nullable=True)
    firmware: Mapped[str | None] = mapped_column(String(255), nullable=True)
    network_zone: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    assessed: Mapped[bool] = mapped_column(Boolean, default=False)


class FindingEntity(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    risk_scenario: Mapped[str] = mapped_column(Text)
    control_gap: Mapped[str] = mapped_column(Text)
    recommended_treatment: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32))
    impact: Mapped[int] = mapped_column(Integer)
    likelihood: Mapped[int] = mapped_column(Integer)
    severity: Mapped[str] = mapped_column(String(32))
    score: Mapped[int] = mapped_column(Integer)
    raised_at: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(160), nullable=True)


class RemediationActionEntity(Base):
    __tablename__ = "remediation_actions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    assigned_to: Mapped[str] = mapped_column(String(160))
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32))
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditEventEntity(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_org_occurred", "organization_id", "occurred_at"),)
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    actor: Mapped[str] = mapped_column(String(160))
    action: Mapped[str] = mapped_column(String(100))
    entity: Mapped[str] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    result: Mapped[str] = mapped_column(String(32))
