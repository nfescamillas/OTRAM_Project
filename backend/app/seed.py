from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from .auth import hash_password
from .entities import AssetEntity, AuditEventEntity, FindingEntity, RemediationActionEntity, SiteEntity, UserEntity
from .models import Severity


ORG_ID = "org-northwind"


def _risk(impact: int, likelihood: int) -> tuple[int, str]:
    score = impact * likelihood
    severity = Severity.LOW if score <= 5 else Severity.MEDIUM if score <= 11 else Severity.HIGH if score <= 19 else Severity.CRITICAL
    return score, severity.value


def seed_database(session: Session, demo_password: str, password_iterations: int, *,
                  sync_demo_password: bool = False) -> None:
    if session.scalar(select(func.count()).select_from(UserEntity)):
        if sync_demo_password:
            password_hash = hash_password(demo_password, iterations=password_iterations)
            session.execute(update(UserEntity).where(UserEntity.email.like("%@otarm.demo"))
                            .values(password_hash=password_hash))
            session.commit()
        return
    password_hash = hash_password(demo_password, iterations=password_iterations)
    session.add_all([
        UserEntity(id="u-assessor", email="assessor@otarm.demo", display_name="Alicia Morgan", role="ASSESSOR", organization_id=ORG_ID, password_hash=password_hash),
        UserEntity(id="u-approver", email="approver@otarm.demo", display_name="Jordan Lee", role="APPROVER", organization_id=ORG_ID, password_hash=password_hash),
        UserEntity(id="u-viewer", email="viewer@otarm.demo", display_name="Taylor Kim", role="VIEWER", organization_id=ORG_ID, password_hash=password_hash),
        UserEntity(id="u-admin", email="admin@otarm.demo", display_name="Morgan Reyes", role="ADMIN", organization_id=ORG_ID, password_hash=password_hash),
    ])
    session.add_all([
        SiteEntity(id="site-north", organization_id=ORG_ID, code="NPR", name="North Process Plant"),
        SiteEntity(id="site-water", organization_id=ORG_ID, code="WTP", name="West Water Plant"),
        SiteEntity(id="site-terminal", organization_id=ORG_ID, code="SBT", name="South Bulk Terminal"),
    ])
    session.flush()
    assets = [
        ("a1","NPR-PLC-014","Boiler Feedwater PLC","PLC","site-north","Utilities","Rockwell Automation","ControlLogix 5580","SAFETY_CRITICAL","SUPPORTED","VERIFIED",date(2026,10,12),"ACTIVE","Maya Chen","v35.011","Cell 2 - Utilities","10.42.20.14",True),
        ("a2","WTP-HMI-003","Clarifier Operator HMI","HMI","site-water","Clarification","Siemens","IPC477E","HIGH","END_OF_SUPPORT","STALE",date(2025,8,4),"ACTIVE","Ethan Cole","Windows 10 LTSC 2019","Cell 1 - Process","10.56.11.23",True),
        ("a3","NPR-SRV-007","Historian Primary","HISTORIAN","site-north","Control Room","Dell","PowerEdge R740","HIGH","LIMITED_SUPPORT","VERIFIED",date(2026,9,21),"ACTIVE","Priya Nair","Historian 2023 R2","Operations DMZ","10.42.40.7",True),
        ("a4","SBT-FW-002","Terminal OT Perimeter","FIREWALL","site-terminal","Main Rack","Palo Alto Networks","PA-3220","SAFETY_CRITICAL","SUPPORTED","VERIFIED",date(2026,10,1),"ACTIVE","Noah Williams","PAN-OS 11.1.4","OT Perimeter","10.73.0.1",True),
        ("a5","WTP-PLC-021","Chemical Dosing PLC","PLC","site-water","Chemical Dosing","Schneider Electric","Modicon M580","SAFETY_CRITICAL","UNKNOWN","UNVERIFIED",None,"ACTIVE",None,"4.10","Cell 3 - Dosing","10.56.30.21",False),
        ("a6","NPR-ENG-005","Turbine Engineering Station","ENGINEERING_WORKSTATION","site-north","Generation","HP","Z4 G4","HIGH","END_OF_LIFE","STALE",date(2024,11,16),"ACTIVE","Maya Chen","Windows Server 2016","Cell 4 - Generation","10.42.44.5",True),
        ("a7","SBT-SW-011","Jetty Access Switch","NETWORK_SWITCH","site-terminal","Jetty 2","Cisco","IE-3300","MEDIUM","SUPPORTED","VERIFIED",date(2026,7,18),"ACTIVE","Noah Williams","IOS XE 17.12","Cell 5 - Jetty","10.73.50.11",False),
        ("a8","WTP-RTU-008","Reservoir Telemetry Gateway","GATEWAY","site-water","Remote Reservoir","Red Lion","FlexEdge DA70","HIGH","UNKNOWN","UNVERIFIED",None,"STANDBY","Ethan Cole","Unknown","Remote Sites","172.22.8.10",False),
    ]
    session.add_all([AssetEntity(id=v[0], tag=v[1], name=v[2], type=v[3], site_id=v[4], area=v[5], vendor=v[6], model=v[7], criticality=v[8], lifecycle=v[9], verification=v[10], last_verified_at=v[11], operational_status=v[12], owner=v[13], firmware=v[14], network_zone=v[15], ip_address=v[16], assessed=v[17], organization_id=ORG_ID) for v in assets])
    session.flush()
    findings = [
        ("f1","a1","Recovery backup not restoration-tested","A controller failure could extend loss of boiler feedwater control if the current backup cannot be restored.","No restoration test evidence for the current logic backup.","Perform an offline restore test and document results.","OPEN",5,4,date(2026,9,18),date(2026,10,10),"Maya Chen"),
        ("f2","a2","Unsupported operator workstation platform","Unsupported platform vulnerabilities could disrupt operator visibility for clarifier operations.","Vendor support ended and no approved isolation exception is recorded.","Upgrade platform or document compensating isolation controls.","TREATMENT_IN_PROGRESS",4,4,date(2026,8,4),date(2026,11,15),"Ethan Cole"),
        ("f3","a6","Shared engineering credentials","Unattributed engineering changes could alter turbine control logic without accountability.","Engineering tool uses a shared privileged account.","Implement named accounts and a controlled emergency credential.","OPEN",5,3,date(2026,7,11),date(2026,9,30),"Maya Chen"),
        ("f4","a4","Remote access rule review overdue","Stale vendor access rules may provide unnecessary paths into the terminal OT zone.","Quarterly rule recertification is overdue.","Complete rule owner review and remove unused entries.","OPEN",4,3,date(2026,9,1),date(2026,10,28),"Noah Williams"),
        ("f5","a3","Historian recovery dependencies incomplete","An infrastructure failure may delay restoration of operational history.","Recovery runbook omits identity and time-source dependencies.","Update and tabletop the recovery runbook.","ACCEPTED",3,2,date(2026,5,6),date(2027,2,1),"Priya Nair"),
    ]
    rows = []
    for value in findings:
        score, severity = _risk(value[7], value[8])
        rows.append(FindingEntity(id=value[0], asset_id=value[1], title=value[2], risk_scenario=value[3], control_gap=value[4], recommended_treatment=value[5], status=value[6], impact=value[7], likelihood=value[8], raised_at=value[9], due_date=value[10], owner=value[11], score=score, severity=severity, organization_id=ORG_ID))
    session.add_all(rows)
    session.flush()
    session.add_all([
        RemediationActionEntity(id="r1", organization_id=ORG_ID, finding_id="f1", title="Run offline controller restore test", assigned_to="Maya Chen", due_date=date(2026,10,10), status="PENDING_VERIFICATION"),
        RemediationActionEntity(id="r2", organization_id=ORG_ID, finding_id="f2", title="Procure supported HMI platform", assigned_to="Ethan Cole", due_date=date(2026,11,15), status="IN_PROGRESS"),
        RemediationActionEntity(id="r3", organization_id=ORG_ID, finding_id="f3", title="Create named engineering accounts", assigned_to="Maya Chen", due_date=date(2026,9,30), status="OPEN"),
        RemediationActionEntity(id="r4", organization_id=ORG_ID, finding_id="f4", title="Recertify OT remote-access rule set", assigned_to="Noah Williams", due_date=date(2026,10,28), status="PLANNED"),
    ])
    session.add_all([
        AuditEventEntity(id="e1", organization_id=ORG_ID, actor="Alicia Morgan", action="ASSESSMENT_FINALIZED", entity="NPR-PLC-014 - OT-BASELINE v1", occurred_at=datetime(2026,10,16,6,42,tzinfo=timezone.utc), result="SUCCESS"),
        AuditEventEntity(id="e2", organization_id=ORG_ID, actor="Maya Chen", action="ACTION_SUBMITTED", entity="Run offline controller restore test", occurred_at=datetime(2026,10,15,23,18,tzinfo=timezone.utc), result="SUCCESS"),
        AuditEventEntity(id="e3", organization_id=ORG_ID, actor="Jordan Lee", action="ASSET_UPDATED", entity="WTP-HMI-003", occurred_at=datetime(2026,10,15,2,5,tzinfo=timezone.utc), result="SUCCESS"),
    ])
    session.commit()
