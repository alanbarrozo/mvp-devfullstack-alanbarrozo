import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "mvp.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "models.sql")
    with get_conn() as conn, open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def ensure_schema():
    with get_conn() as conn:
        def has_col(table, col):
            cols = {r["name"]
                    for r in conn.execute(f"PRAGMA table_info({table})")}
            return col in cols

        # adicionar colunas SEM default (evita o erro do SQLite)
        if not has_col("donos", "created_at"):
            conn.execute("ALTER TABLE donos ADD COLUMN created_at TEXT")
        if not has_col("cachorros", "created_at"):
            conn.execute("ALTER TABLE cachorros ADD COLUMN created_at TEXT")
        if not has_col("cachorros", "foto_url"):
            conn.execute("ALTER TABLE cachorros ADD COLUMN foto_url TEXT")

        # preencher registros antigos com timestamp atual
        conn.execute(
            "UPDATE donos SET created_at = COALESCE(created_at, datetime('now'))")
        conn.execute(
            "UPDATE cachorros SET created_at = COALESCE(created_at, datetime('now'))")

        # índices (idempotentes)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uniq_cao_por_dono ON cachorros(dono_id, nome_cachorro, idade)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cachorros_dono ON cachorros(dono_id)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cachorros_nome ON cachorros(nome_cachorro)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cachorros_raca ON cachorros(raca)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_donos_lookup ON donos(nome_completo, bloco, apartamento)")
        conn.commit()
