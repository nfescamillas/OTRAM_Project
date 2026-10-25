from __future__ import annotations

from pathlib import Path
from time import perf_counter

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .telemetry import ApplicationMetrics


class Base(DeclarativeBase):
    pass


def default_database_url() -> str:
    path = Path(__file__).resolve().parents[1] / "otarm.db"
    return f"sqlite:///{path.as_posix()}"


def normalize_database_url(database_url: str) -> str:
    """Select Psycopg 3 explicitly for common PostgreSQL URL forms."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def create_database_engine(database_url: str) -> Engine:
    database_url = normalize_database_url(database_url)
    url = make_url(database_url)
    options: dict[str, object] = {"pool_pre_ping": True}
    if url.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False}
        if url.database in {None, "", ":memory:"}:
            options["poolclass"] = StaticPool
    engine = create_engine(database_url, **options)
    if url.get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def instrument_database(engine: Engine, metrics: ApplicationMetrics) -> None:
    """Measure SQL execution without recording statements or record identifiers."""
    existing_state = getattr(engine, "_otarm_metrics_state", None)
    if existing_state is not None:
        existing_state["metrics"] = metrics
        return

    state = {"metrics": metrics}
    setattr(engine, "_otarm_metrics_state", state)
    backend = engine.url.get_backend_name()

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(_connection, _cursor, statement, _parameters, context, _executemany) -> None:
        context._otarm_started_at = perf_counter()
        context._otarm_operation = statement.lstrip().partition(" ")[0].upper() or "UNKNOWN"

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(_connection, _cursor, _statement, _parameters, context, _executemany) -> None:
        started_at = getattr(context, "_otarm_started_at", perf_counter())
        state["metrics"].db_duration.record(perf_counter() - started_at, {
            "db.system.name": backend,
            "db.operation.name": getattr(context, "_otarm_operation", "UNKNOWN"),
        })

    @event.listens_for(engine, "handle_error")
    def handle_error(exception_context) -> None:
        context = exception_context.execution_context
        attributes = {
            "db.system.name": backend,
            "db.operation.name": getattr(context, "_otarm_operation", "UNKNOWN"),
        }
        state["metrics"].db_errors.add(1, attributes)
        if context is not None:
            started_at = getattr(context, "_otarm_started_at", perf_counter())
            state["metrics"].db_duration.record(perf_counter() - started_at, attributes)
