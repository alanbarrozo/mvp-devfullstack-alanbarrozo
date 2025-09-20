from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flasgger import Swagger
from db import get_conn, init_db, ensure_schema
import sqlite3
from werkzeug.exceptions import HTTPException
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os


app = Flask(__name__)
CORS(app)  # habilita CORS para permitir o front abrir via file:// e chamar a API

app.config["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB por arquivo
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["SWAGGER"] = {"title": "API — Cães do Condomínio", "uiversion": 3}
swagger = Swagger(app)

init_db()  # garante que a tabela 'cachorros' exista antes de receber requests
ensure_schema()

FMT = "%Y-%m-%d %H:%M:%S"
TZ_BR = ZoneInfo("America/Sao_Paulo")


def _parse_sqlite_utc(ts: str) -> datetime:
    # nossas colunas created_at vêm do SQLite como UTC ("YYYY-MM-DD HH:MM:SS")
    return datetime.strptime(ts, FMT).replace(tzinfo=timezone.utc)


def _to_br_str(ts: str) -> str:
    # recebe o texto UTC do SQLite e devolve string no fuso de Brasília
    return _parse_sqlite_utc(ts).astimezone(TZ_BR).strftime(FMT)


@app.errorhandler(sqlite3.Error)
def handle_sqlite_error(e):
    # Ex.: database is locked, file missing, permissão etc.
    return jsonify(erro="Banco de dados indisponível no momento. Tente novamente em instantes."), 503


@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify(erro=e.description), e.code


@app.errorhandler(Exception)
def handle_unexpected(e):
    print("Unhandled error:", e)  # log simples
    return jsonify(erro="Erro interno do servidor"), 500


def get_or_create_dono(conn, nome_completo, bloco, apartamento):
    row = conn.execute(
        "SELECT id FROM donos WHERE nome_completo=? AND bloco=? AND apartamento=?",
        (nome_completo, bloco, apartamento)
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO donos(nome_completo, bloco, apartamento, created_at) VALUES (?,?,?, datetime('now'))",
        (nome_completo, bloco, apartamento)
    )
    return cur.lastrowid


@app.get("/status")
def status():
    return jsonify(ok=True, versão="0.1.0")


@app.post("/cachorros")
def criar_cachorro():
    """
Cadastrar um cachorro
---
tags:
  - Cachorros
summary: Cadastra um novo cachorro (com dados do dono)
consumes:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - nome_cachorro
        - raca
        - idade
        - dono
      properties:
        nome_cachorro:
          type: string
        raca:
          type: string
        idade:
          type: integer
          minimum: 0
        dono:
          type: object
          required:
            - nome_completo
            - bloco
            - apartamento
          properties:
            nome_completo: { type: string }
            bloco: { type: string }
            apartamento: { type: string }
    example:
      nome_cachorro: Rex
      raca: Vira-lata
      idade: 3
      dono:
        nome_completo: Ana Souza
        bloco: B
        apartamento: "203"
responses:
  201:
    description: Criado com sucesso
  400:
    description: Erro de validação
  409:
    description: "Conflito (duplicidade: mesmo dono + nome + idade)"
"""

    data = request.get_json(force=True, silent=True) or {}

    # aceita { dono:{...}, nome_cachorro, raca, idade } OU achatado
    dono = data.get("dono") or {}
    nome_completo = (dono.get("nome_completo")
                     or data.get("nome_completo") or "").strip()
    bloco = (dono.get("bloco") or data.get("bloco") or "").strip()
    apartamento = (dono.get("apartamento")
                   or data.get("apartamento") or "").strip()

    nome_cachorro = (data.get("nome_cachorro") or "").strip()
    raca = (data.get("raca") or "").strip()
    idade = data.get("idade")

    if not all([nome_completo, bloco, apartamento, nome_cachorro, raca]) or idade is None:
        return {"erro": "Campos obrigatórios: dono(nome_completo, bloco, apartamento) e cachorro(nome_cachorro, raca, idade)"}, 400
    try:
        idade = int(idade)
        if idade < 0:
            return {"erro": "idade deve ser >= 0"}, 400
    except (ValueError, TypeError):
        return {"erro": "idade deve ser um número inteiro"}, 400

    with get_conn() as conn:
        dono_id = get_or_create_dono(conn, nome_completo, bloco, apartamento)
        try:
            cur = conn.execute(
                "INSERT INTO cachorros(nome_cachorro, raca, idade, dono_id, created_at) VALUES (?,?,?,?, datetime('now'))",
                (nome_cachorro, raca, idade, dono_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return {"erro": "Já existe um cachorro com o mesmo nome e idade para este dono."}, 409

        novo_id = cur.lastrowid
        row = conn.execute("""
            SELECT c.id, c.nome_cachorro, c.raca, c.idade,
                   c.created_at, c.foto_url,
                   d.nome_completo, d.bloco, d.apartamento,
                   d.created_at AS dono_created_at
            FROM cachorros c
            JOIN donos d ON d.id = c.dono_id
            WHERE c.id = ?
        """, (novo_id,)).fetchone()

    it = dict(row)
    if it.get("created_at"):
        try:
            it["created_at_br"] = _to_br_str(it["created_at"])
        except Exception:
            pass
    if it.get("dono_created_at"):
        try:
            it["dono_created_at_br"] = _to_br_str(it["dono_created_at"])
        except Exception:
            pass
    return it, 201


@app.get("/cachorros")
def listar_cachorros():
    """
Listar cachorros
---
tags: [Cachorros]
summary: Lista todos os cachorros com dados do dono
responses:
  200: {description: Lista de cachorros}
"""
    with get_conn() as conn:
        rows = conn.execute("""
           SELECT c.id, c.nome_cachorro, c.raca, c.idade,
                  c.created_at, c.foto_url,
                  d.nome_completo, d.bloco, d.apartamento,
                  d.created_at AS dono_created_at
           FROM cachorros c
           JOIN donos d ON d.id = c.dono_id
           ORDER BY c.id DESC
        """).fetchall()
    data = [dict(r) for r in rows]
    for it in data:
        if it.get("created_at"):
            try:
                it["created_at_br"] = _to_br_str(it["created_at"])
            except Exception:
                pass
        if it.get("dono_created_at"):
            try:
                it["dono_created_at_br"] = _to_br_str(it["dono_created_at"])
            except Exception:
                pass
    return data, 200


@app.get("/cachorros/<int:cachorro_id>")
def obter_cachorro(cachorro_id):
    """
Obter cachorro por ID
---
tags:
  - Cachorros
summary: Retorna um cachorro com os dados do dono
parameters:
  - in: path
    name: cachorro_id
    type: integer
    required: true
responses:
  200:
    description: Cachorro encontrado
  404:
    description: Não encontrado
"""

    with get_conn() as conn:
        row = conn.execute("""
           SELECT c.id, c.nome_cachorro, c.raca, c.idade,
                  c.created_at, c.foto_url,
                  d.nome_completo, d.bloco, d.apartamento,
                  d.created_at AS dono_created_at
           FROM cachorros c
           JOIN donos d ON d.id = c.dono_id
           WHERE c.id = ?
        """, (cachorro_id,)).fetchone()
        if not row:
            return {"erro": "não encontrado"}, 404

    it = dict(row)
    if it.get("created_at"):
        try:
            it["created_at_br"] = _to_br_str(it["created_at"])
        except Exception:
            pass
    if it.get("dono_created_at"):
        try:
            it["dono_created_at_br"] = _to_br_str(it["dono_created_at"])
        except Exception:
            pass
    return it, 200


@app.delete("/cachorros/<int:cachorro_id>")
def deletar_cachorro(cachorro_id):
    """
Deletar cachorro por ID
---
tags:
  - Cachorros
summary: Remove um cachorro pelo ID
parameters:
  - in: path
    name: cachorro_id
    type: integer
    required: true
responses:
  204:
    description: Excluído
  404:
    description: Não encontrado
"""


    with get_conn() as conn:
        cur = conn.execute("DELETE FROM cachorros WHERE id=?", (cachorro_id,))
        conn.commit()
        if cur.rowcount == 0:
            return {"erro": "não encontrado"}, 404
        return "", 204


@app.get("/donos")
def listar_donos():
    """
    Listar donos (com contagem de cachorros)
    ---
    tags:
      - Cachorros
    summary: Retorna cada dono e a quantidade de cachorros que possui
    responses:
      200:
        description: Lista de donos com contagem
        schema:
          type: array
          items:
            type: object
            properties:
              id: {type: integer, example: 1}
              nome_completo: {type: string, example: Ana Souza}
              bloco: {type: string, example: B}
              apartamento: {type: string, example: "203"}
              quantidade_cachorros: {type: integer, example: 2}
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT d.id, d.nome_completo, d.bloco, d.apartamento,
                   COUNT(c.id) AS quantidade_cachorros
            FROM donos d
            LEFT JOIN cachorros c ON c.dono_id = d.id
            GROUP BY d.id, d.nome_completo, d.bloco, d.apartamento
            ORDER BY d.nome_completo COLLATE NOCASE
        """).fetchall()
        return [dict(r) for r in rows], 200


def _humanize_delta_secs(seconds: float) -> str:
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds} segundo(s)"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minuto(s)"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hora(s)"
    days = hours // 24
    if days < 30:
        return f"{days} dia(s)"
    months = days // 30
    if months < 12:
        return f"{months} mês(es)"
    years = months // 12
    return f"{years} ano(s)"


def _parse_sqlite_ts(ts: str) -> datetime:
    # nossas colunas created_at são do tipo "YYYY-MM-DD HH:MM:SS" (UTC)
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


@app.get("/donos/<int:dono_id>")
def obter_dono(dono_id):
    """
Detalhe do dono (com tempos de cadastro)
---
tags:
  - Cachorros
summary: Retorna dados do dono e seus cachorros
parameters:
  - in: path
    name: dono_id
    type: integer
    required: true
responses:
  200:
    description: Dono encontrado
  404:
    description: Não encontrado
"""

    with get_conn() as conn:
        dono = conn.execute("""
            SELECT id, nome_completo, bloco, apartamento, created_at
              FROM donos
             WHERE id = ?
        """, (dono_id,)).fetchone()

        if not dono:
            return {"erro": "não encontrado"}, 404

        dogs = conn.execute("""
            SELECT id, nome_cachorro, raca, idade, created_at, foto_url
              FROM cachorros
             WHERE dono_id = ?
             ORDER BY id DESC
        """, (dono_id,)).fetchall()

    now_br = datetime.now(TZ_BR)

    # dono: converter created_at para BR e calcular "há quanto tempo"
    dono_created_br_str = _to_br_str(dono["created_at"])
    dono_created_br_dt = datetime.strptime(
        dono_created_br_str, FMT).replace(tzinfo=TZ_BR)
    dono_secs = (now_br - dono_created_br_dt).total_seconds()

    lista = []
    for d in dogs:
        created_br_str = _to_br_str(d["created_at"])
        created_br_dt = datetime.strptime(
            created_br_str, FMT).replace(tzinfo=TZ_BR)
        secs = (now_br - created_br_dt).total_seconds()

        item = dict(d)
        item["created_at_br"] = created_br_str
        item["tempo_cadastrado"] = _humanize_delta_secs(secs)
        lista.append(item)

    return {
        "id": dono["id"],
        "nome_completo": dono["nome_completo"],
        "bloco": dono["bloco"],
        "apartamento": dono["apartamento"],
        "created_at": dono["created_at"],        # UTC original (mantido)
        "created_at_br": dono_created_br_str,    # NOVO: Brasília
        "tempo_cadastrado": _humanize_delta_secs(dono_secs),
        "quantidade_cachorros": len(lista),
        "cachorros": lista
    }, 200


@app.put("/cachorros/<int:cachorro_id>")
def atualizar_cachorro(cachorro_id):
    """
Atualizar cachorro por ID
---
tags:
  - Cachorros
summary: Atualiza dados do cachorro e, opcionalmente, do dono
consumes:
  - application/json
parameters:
  - in: path
    name: cachorro_id
    type: integer
    required: true
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        nome_cachorro: { type: string }
        raca: { type: string }
        idade: { type: integer, minimum: 0 }
        dono:
          type: object
          properties:
            nome_completo: { type: string }
            bloco: { type: string }
            apartamento: { type: string }
    example:
      nome_cachorro: Thor
      idade: 4
      dono:
        nome_completo: Ana Souza
        bloco: B
        apartamento: "203"
responses:
  200:
    description: Registro atualizado
  400:
    description: Erro de validação
  404:
    description: Não encontrado
  409:
    description: "Conflito (duplicidade: mesmo dono + nome + idade)"
"""

    data = request.get_json(force=True, silent=True) or {}

    with get_conn() as conn:
        atual = conn.execute(
            "SELECT * FROM cachorros WHERE id=?", (cachorro_id,)).fetchone()
        if not atual:
            return {"erro": "não encontrado"}, 404

        # valores atuais como fallback
        nome_cachorro = (data.get("nome_cachorro")
                         or atual["nome_cachorro"]).strip()
        raca = (data.get("raca") or atual["raca"]).strip()
        idade_val = data.get("idade", atual["idade"])
        try:
            idade = int(idade_val)
            if idade < 0:
                return {"erro": "idade deve ser >= 0"}, 400
        except (ValueError, TypeError):
            return {"erro": "idade deve ser um número inteiro"}, 400

        # dono (opcional): se veio qualquer campo, exigir os 3
        dono = data.get("dono") or {}
        if any(k in dono for k in ("nome_completo", "bloco", "apartamento")):
            nome_completo = (dono.get("nome_completo") or "").strip()
            bloco = (dono.get("bloco") or "").strip()
            apartamento = (dono.get("apartamento") or "").strip()
            if not all([nome_completo, bloco, apartamento]):
                return {"erro": "Para atualizar o dono, informe nome_completo, bloco e apartamento."}, 400
            dono_id = get_or_create_dono(
                conn, nome_completo, bloco, apartamento)
        else:
            dono_id = atual["dono_id"]

        # aplica a atualização (protege duplicidade com UNIQUE + 409)
        try:
            conn.execute("""
                UPDATE cachorros
                   SET nome_cachorro=?, raca=?, idade=?, dono_id=?
                 WHERE id=?
            """, (nome_cachorro, raca, idade, dono_id, cachorro_id))
            conn.commit()
        except sqlite3.IntegrityError:
            return {"erro": "Já existe um cachorro com o mesmo nome e idade para este dono."}, 409

        # retorna registro atualizado (com campos extras e horário BR se disponível)
        row = conn.execute("""
            SELECT c.id, c.nome_cachorro, c.raca, c.idade,
                   c.created_at, c.foto_url,
                   d.nome_completo, d.bloco, d.apartamento,
                   d.created_at AS dono_created_at
              FROM cachorros c
              JOIN donos d ON d.id = c.dono_id
             WHERE c.id = ?
        """, (cachorro_id,)).fetchone()

        it = dict(row)
        # adiciona conversões para Brasília se helpers existirem
        if it.get("created_at"):
            try:
                it["created_at_br"] = _to_br_str(it["created_at"])
            except Exception:
                pass
        if it.get("dono_created_at"):
            try:
                it["dono_created_at_br"] = _to_br_str(it["dono_created_at"])
            except Exception:
                pass
        return it, 200


@app.get("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.post("/cachorros/<int:cachorro_id>/foto")
def upload_foto(cachorro_id):
    """
Upload de foto do cachorro
---
tags:
  - Cachorros
summary: "Envia a imagem do cachorro e associa ao registro"
consumes:
  - multipart/form-data
parameters:
  - in: path
    name: cachorro_id
    type: integer
    required: true
  - in: formData
    name: foto
    type: file
    required: true
responses:
  200:
    description: Foto enviada com sucesso
  400:
    description: Arquivo inválido
  404:
    description: Não encontrado
"""

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM cachorros WHERE id=?", (cachorro_id,)).fetchone()
        if not row:
            return {"erro": "não encontrado"}, 404

    f = request.files.get("foto")
    if not f or not f.filename:
        return {"erro": "Envie o arquivo no campo 'foto'."}, 400

    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return {"erro": "Formato inválido. Use png, jpg, jpeg ou webp."}, 400

    fname = f"cao_{cachorro_id}.{ext}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    f.save(path)

    foto_url = f"/uploads/{fname}"
    with get_conn() as conn:
        conn.execute("UPDATE cachorros SET foto_url=? WHERE id=?",
                     (foto_url, cachorro_id))
        conn.commit()

    return {"ok": True, "foto_url": foto_url}, 200


if __name__ == "__main__":
    app.run(debug=True)
