from __future__ import annotations

from datetime import date, datetime
from typing import Final

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Date as SqlDate,
)
from sqlalchemy import (
    DateTime as SqlDateTime,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.ddl import CreateTable


class Base(DeclarativeBase):
    pass


class PlatformIdentity(Base):
    __tablename__ = "platform_identity"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_uid: Mapped[int] = mapped_column(Integer)
    install_id: Mapped[str] = mapped_column(String(128), unique=True)
    installed_version: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[date] = mapped_column(SqlDate)


class Provider(Base):
    __tablename__ = "provider"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    created_at: Mapped[date] = mapped_column(SqlDate)


class ProviderEndpoint(Base):
    __tablename__ = "provider_endpoint"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("provider.id"))
    endpoint_id: Mapped[str] = mapped_column(String(255))
    allowed_host: Mapped[str] = mapped_column(String(255))
    allowed_port: Mapped[int]
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (UniqueConstraint("provider_id", "endpoint_id"),)


class AdapterInstallation(Base):
    __tablename__ = "adapter_installation"

    id: Mapped[int] = mapped_column(primary_key=True)
    package: Mapped[str] = mapped_column(String(255), unique=True)
    version: Mapped[str] = mapped_column(String(128))
    contract_version: Mapped[str] = mapped_column(String(128))
    compatible: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[date] = mapped_column(SqlDate)


class CredentialReference(Base):
    __tablename__ = "credential_reference"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("provider.id"))
    keychain_service: Mapped[str] = mapped_column(String(255))
    keychain_account: Mapped[str] = mapped_column(String(255))
    display_label: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (UniqueConstraint("provider_id", "keychain_service", "keychain_account"),)


class ComplianceProfileVersion(Base):
    __tablename__ = "compliance_profile_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("provider.id"))
    version_id: Mapped[str] = mapped_column(String(128))
    data_source: Mapped[str] = mapped_column(String(512))
    account_type: Mapped[str] = mapped_column(String(64))
    permitted_purposes: Mapped[list[str]] = mapped_column(JSON)
    retention_permission: Mapped[str] = mapped_column(String(64))
    export_permission: Mapped[str] = mapped_column(String(64))
    confirmed_at: Mapped[datetime] = mapped_column(SqlDateTime(timezone=True))
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (UniqueConstraint("provider_id", "version_id"),)


class SecurityIdentity(Base):
    __tablename__ = "security_identity"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_security_id: Mapped[str] = mapped_column(String(255), unique=True)
    market: Mapped[str] = mapped_column(String(64))
    instrument_type: Mapped[str] = mapped_column(String(64))
    local_code: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (UniqueConstraint("market", "instrument_type", "local_code"),)


class SecurityMasterVersion(Base):
    __tablename__ = "security_master_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[str] = mapped_column(String(128), unique=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security_identity.id"))
    name: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(8))
    listing_date: Mapped[date] = mapped_column(SqlDate)
    termination_date: Mapped[date | None] = mapped_column(SqlDate)
    status: Mapped[str] = mapped_column(String(32))
    valid_from: Mapped[date] = mapped_column(SqlDate)
    valid_to: Mapped[date | None] = mapped_column(SqlDate)
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (CheckConstraint("valid_to IS NULL OR valid_to >= valid_from"),)


class SecurityMappingVersion(Base):
    __tablename__ = "security_mapping_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[str] = mapped_column(String(128), unique=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("provider.id"))
    provider_identifier: Mapped[str] = mapped_column(String(255))
    security_id: Mapped[int] = mapped_column(ForeignKey("security_identity.id"))
    valid_from: Mapped[date] = mapped_column(SqlDate)
    valid_to: Mapped[date] = mapped_column(SqlDate)
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (
        UniqueConstraint("provider_id", "provider_identifier", "valid_from"),
        CheckConstraint("valid_to >= valid_from"),
    )


class CalendarVersion(Base):
    __tablename__ = "calendar_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[str] = mapped_column(String(128), unique=True)
    calendar_type: Mapped[str] = mapped_column(String(64))
    market: Mapped[str] = mapped_column(String(64))
    timezone_name: Mapped[str] = mapped_column(String(128))
    valid_from: Mapped[date] = mapped_column(SqlDate)
    valid_to: Mapped[date] = mapped_column(SqlDate)
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (
        UniqueConstraint("calendar_type", "market", "valid_from"),
        CheckConstraint("valid_to >= valid_from"),
    )


class CalendarDay(Base):
    __tablename__ = "calendar_day"

    id: Mapped[int] = mapped_column(primary_key=True)
    calendar_id: Mapped[int] = mapped_column(ForeignKey("calendar_version.id"))
    observation_date: Mapped[date] = mapped_column(SqlDate)
    open: Mapped[bool] = mapped_column(Boolean)
    session: Mapped[str] = mapped_column(String(64))
    tradability: Mapped[str] = mapped_column(String(64))

    __table_args__ = (UniqueConstraint("calendar_id", "observation_date"),)


class CorporateAction(Base):
    __tablename__ = "corporate_action"

    id: Mapped[int] = mapped_column(primary_key=True)
    action_id: Mapped[str] = mapped_column(String(128), unique=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security_identity.id"))
    source_type: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[str] = mapped_column(String(255))
    effective_date: Mapped[date] = mapped_column(SqlDate)
    retrieved_at: Mapped[datetime] = mapped_column(SqlDateTime(timezone=True))
    value: Mapped[float] = mapped_column(Numeric(38, 12))
    version_id: Mapped[str] = mapped_column(String(128))


class FactorSeries(Base):
    __tablename__ = "factor_series"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[str] = mapped_column(String(128), unique=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security_identity.id"))
    adjustment_mode: Mapped[str] = mapped_column(String(64))
    valid_from: Mapped[date] = mapped_column(SqlDate)
    valid_to: Mapped[date] = mapped_column(SqlDate)
    created_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (CheckConstraint("valid_to >= valid_from"),)


class FactorPoint(Base):
    __tablename__ = "factor_point"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("factor_series.id"))
    observation_date: Mapped[date] = mapped_column(SqlDate)
    factor: Mapped[float] = mapped_column(Numeric(38, 12))
    provider: Mapped[str] = mapped_column(String(128))
    retrieved_at: Mapped[datetime] = mapped_column(SqlDateTime(timezone=True))
    version_id: Mapped[str] = mapped_column(String(128))

    __table_args__ = (UniqueConstraint("series_id", "observation_date"),)


class IngestionRun(Base):
    __tablename__ = "ingestion_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(128), unique=True)
    provider: Mapped[str] = mapped_column(String(128))
    data_kind: Mapped[str] = mapped_column(String(64))
    refresh: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING")
    planned_count: Mapped[int]
    created_count: Mapped[int] = mapped_column(default=0)
    updated_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    resumable_boundary: Mapped[date | None] = mapped_column(SqlDate)
    provider_failure: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[date] = mapped_column(SqlDate)


class IngestionFinalizedDate(Base):
    __tablename__ = "ingestion_finalized_date"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_run.id"))
    security_id: Mapped[int] = mapped_column(ForeignKey("security_identity.id"))
    data_kind: Mapped[str] = mapped_column(String(64))
    expected_date: Mapped[date] = mapped_column(SqlDate)
    outcome: Mapped[str] = mapped_column(String(64))

    __table_args__ = (UniqueConstraint("run_id", "security_id", "data_kind", "expected_date"),)


class LogicalObservation(Base):
    __tablename__ = "logical_observation"

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security_identity.id"))
    data_kind: Mapped[str] = mapped_column(String(64))
    observation_date: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (UniqueConstraint("security_id", "data_kind", "observation_date"),)


class ObservationVersion(Base):
    __tablename__ = "observation_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    logical_id: Mapped[int] = mapped_column(ForeignKey("logical_observation.id"))
    version_id: Mapped[str] = mapped_column(String(128), unique=True)
    previous_version_id: Mapped[str | None] = mapped_column(String(128))
    object_hash: Mapped[str] = mapped_column(String(128))
    row_locator: Mapped[str] = mapped_column(String(255))
    normalized_value_hash: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(128))
    provider_identifier: Mapped[str] = mapped_column(String(255))
    source_version: Mapped[str | None] = mapped_column(String(255))
    retrieved_at: Mapped[datetime] = mapped_column(SqlDateTime(timezone=True))


class QualityRuleSet(Base):
    __tablename__ = "quality_rule_set"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(128))
    version_id: Mapped[str] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(32))
    plan_impact: Mapped[str] = mapped_column(String(32), default="BLOCK")
    provenance_level: Mapped[str] = mapped_column(String(64), default="REGENERATABLE")
    remediation: Mapped[str] = mapped_column(String(64), default="INVESTIGATE")
    created_at: Mapped[date] = mapped_column(SqlDate)


class QualityAssessment(Base):
    __tablename__ = "quality_assessment"

    id: Mapped[int] = mapped_column(primary_key=True)
    observation_version_id: Mapped[int] = mapped_column(ForeignKey("observation_version.id"))
    rule_set_id: Mapped[int] = mapped_column(ForeignKey("quality_rule_set.id"))
    status: Mapped[str] = mapped_column(String(32))
    assessed_at: Mapped[date] = mapped_column(SqlDate)


class QualityIssue(Base):
    __tablename__ = "quality_issue"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("quality_assessment.id"))
    security_id: Mapped[int] = mapped_column(ForeignKey("security_identity.id"))
    observation_date: Mapped[date] = mapped_column(SqlDate)
    affected_field: Mapped[str] = mapped_column(String(128))
    observed_value: Mapped[str] = mapped_column(String(512))
    missing_input: Mapped[str | None] = mapped_column(String(64))


class DatasetVersion(Base):
    __tablename__ = "dataset_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[str] = mapped_column(String(128), unique=True)
    parent_dataset: Mapped[str] = mapped_column(String(128))
    manifest_hash: Mapped[str] = mapped_column(String(128))
    row_count: Mapped[int] = mapped_column(Integer)
    schema_id: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[date] = mapped_column(SqlDate)


class DatasetObjectRef(Base):
    __tablename__ = "dataset_object_ref"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_version_id: Mapped[int] = mapped_column(ForeignKey("dataset_version.id"))
    object_hash: Mapped[str] = mapped_column(String(128))
    row_count: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(128))

    __table_args__ = (UniqueConstraint("dataset_version_id", "object_hash"),)


class DataSnapshot(Base):
    __tablename__ = "data_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(128), unique=True)
    dataset_version_id: Mapped[int] = mapped_column(ForeignKey("dataset_version.id"))
    snapshot_hash: Mapped[str] = mapped_column(String(128))
    manifest_json: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[date] = mapped_column(SqlDate)


class SnapshotConfirmation(Base):
    __tablename__ = "snapshot_confirmation"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("data_snapshot.id"))
    owner_uid: Mapped[int] = mapped_column(Integer)
    confirmed_at: Mapped[date] = mapped_column(SqlDate)

    __table_args__ = (UniqueConstraint("snapshot_id", "owner_uid"),)


class ResearchManifest(Base):
    __tablename__ = "research_manifest"

    id: Mapped[int] = mapped_column(primary_key=True)
    manifest_id: Mapped[str] = mapped_column(String(128), unique=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("data_snapshot.id"))
    manifest_json: Mapped[dict[str, object]] = mapped_column(JSON)
    manifest_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[date] = mapped_column(SqlDate)


class ResearchRun(Base):
    __tablename__ = "research_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    manifest_id: Mapped[int] = mapped_column(ForeignKey("research_manifest.id"))
    status: Mapped[str] = mapped_column(String(32), default="READY")
    created_at: Mapped[date] = mapped_column(SqlDate)


class ResultObject(Base):
    __tablename__ = "result_object"

    id: Mapped[int] = mapped_column(primary_key=True)
    research_run_id: Mapped[int] = mapped_column(ForeignKey("research_run.id"))
    object_hash: Mapped[str] = mapped_column(String(128))
    format_name: Mapped[str] = mapped_column(String(64), default="jsonl")
    row_count: Mapped[int] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("research_run_id", "object_hash"),)


class BackupManifest(Base):
    __tablename__ = "backup_manifest"

    id: Mapped[int] = mapped_column(primary_key=True)
    manifest_id: Mapped[str] = mapped_column(String(128), unique=True)
    schema_version: Mapped[str] = mapped_column(String(128))
    item_counts: Mapped[dict[str, int]] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(128))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    restorable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[date] = mapped_column(SqlDate)


class MigrationHistory(Base):
    __tablename__ = "migration_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(128))
    layout_version: Mapped[str] = mapped_column(String(128))
    backup_manifest_id: Mapped[str] = mapped_column(String(128))
    completed_at: Mapped[date] = mapped_column(SqlDate)


APPEND_ONLY_TABLES: Final[frozenset[str]] = frozenset(
    {
        "compliance_profile_version",
        "security_master_version",
        "security_mapping_version",
        "calendar_version",
        "calendar_day",
        "corporate_action",
        "factor_series",
        "factor_point",
        "ingestion_finalized_date",
        "logical_observation",
        "observation_version",
        "quality_assessment",
        "quality_issue",
        "dataset_version",
        "dataset_object_ref",
        "data_snapshot",
        "research_manifest",
        "result_object",
        "migration_history",
    }
)


def create_sql_schema(engine: Engine) -> None:
    """Create all schema objects and immutable-state guardrails."""
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for table_name in sorted(APPEND_ONLY_TABLES):
            _create_guard(connection, table_name, "UPDATE")
            _create_guard(connection, table_name, "DELETE")


def schema_sql(engine: Engine) -> str:
    dialect = engine.dialect
    statements: list[str] = []
    for table in sorted(Base.metadata.tables.values(), key=lambda item: item.name):
        statements.append(str(CreateTable(table).compile(dialect=dialect)))
    for table_name in sorted(APPEND_ONLY_TABLES):
        statements.append(guard_sql(table_name, "UPDATE"))
        statements.append(guard_sql(table_name, "DELETE"))
    return "\n".join(f"{statement};" for statement in statements)


def guard_sql(table_name: str, action: str) -> str:
    return (
        f"CREATE TRIGGER IF NOT EXISTS {table_name}_{action.lower()}_rejection "
        f"BEFORE {action} ON {table_name} "
        f"BEGIN SELECT RAISE(ABORT, '{table_name} is append-only'); END;"
    )


def _create_guard(connection: object, table_name: str, action: str) -> None:
    if hasattr(connection, "execute"):
        connection.execute(text(guard_sql(table_name, action)))
