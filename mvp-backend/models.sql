PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS donos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome_completo TEXT NOT NULL,
  bloco TEXT NOT NULL,
  apartamento TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cachorros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome_cachorro TEXT NOT NULL,
  raca TEXT NOT NULL,
  idade INTEGER NOT NULL CHECK (idade >= 0),
  dono_id INTEGER NOT NULL,
  FOREIGN KEY (dono_id) REFERENCES donos(id) ON DELETE CASCADE
);


-- evitar duplicatas de cão por dono (mesmo nome+idade)
CREATE UNIQUE INDEX IF NOT EXISTS uniq_cao_por_dono
  ON cachorros(dono_id, nome_cachorro, idade);

-- (já ajuda performance também)
CREATE INDEX IF NOT EXISTS idx_cachorros_dono ON cachorros(dono_id);
CREATE INDEX IF NOT EXISTS idx_cachorros_nome ON cachorros(nome_cachorro);
CREATE INDEX IF NOT EXISTS idx_cachorros_raca ON cachorros(raca);
CREATE INDEX IF NOT EXISTS idx_donos_lookup   ON donos(nome_completo, bloco, apartamento);

