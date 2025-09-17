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
