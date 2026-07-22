"""Moteur SQLite + session SQLAlchemy 2.0.

SQLite en fichier (WAL) dans /data. Les FK sont activées explicitement
(SQLite ne les applique pas par défaut) pour que ON DELETE CASCADE marche.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DB_PATH

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base déclarative commune à tous les modèles ORM."""


def get_db() -> Iterator[Session]:
    """Dépendance FastAPI : ouvre une session par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations() -> None:
    """Migrations légères pour les DB existantes (SQLite, sans Alembic).

    create_all() crée les tables absentes mais n'ajoute pas les colonnes
    ajoutées après coup à une table existante -> on le fait à la main.
    """
    from sqlalchemy import text

    with engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(recipes)").fetchall()
        }
        if "categorie_plat" not in cols:
            conn.exec_driver_sql("ALTER TABLE recipes ADD COLUMN categorie_plat TEXT")
        if "favori" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE recipes ADD COLUMN favori INTEGER DEFAULT 0"
            )


def init_db() -> None:
    """Crée les tables si absentes, migre, puis seed les données par défaut."""
    from . import models  # noqa: F401  (enregistre les tables)
    from .seed import seed_defaults

    Base.metadata.create_all(bind=engine)
    _run_migrations()
    with SessionLocal() as db:
        seed_defaults(db)
        db.commit()
