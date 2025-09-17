from flask import Flask, jsonify, request
from flask_cors import CORS
from flasgger import Swagger
from db import get_conn, init_db


app = Flask(__name__)
CORS(app)  # habilita CORS para permitir o front abrir via file:// e chamar a API

app.config["SWAGGER"] = {"title": "API — Cães do Condomínio", "uiversion": 3}
swagger = Swagger(app)

init_db()  # garante que a tabela 'cachorros' exista antes de receber requests


def get_or_create_dono(conn, nome_completo, bloco, apartamento):
    row = conn.execute(
        "SELECT id FROM donos WHERE nome_completo=? AND bloco=? AND apartamento=?",
        (nome_completo, bloco, apartamento)
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO donos(nome_completo, bloco, apartamento) VALUES (?,?,?)",
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
description: Recebe os dados do cachorro e do dono, cria (ou reaproveita) o dono e vincula via dono_id.
consumes:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required: [nome_cachorro, raca, idade, dono]
      properties:
        nome_cachorro:
          type: string
          example: Thor
        raca:
          type: string
          example: Labrador
        idade:
          type: integer
          minimum: 0
          example: 2
        dono:
          type: object
          required: [nome_completo, bloco, apartamento]
          properties:
            nome_completo:
              type: string
              example: Ana Souza
            bloco:
              type: string
              example: B
            apartamento:
              type: string
              example: "203"
responses:
  201:
    description: Criado com sucesso
    schema:
      type: object
      properties:
        id: {type: integer, example: 7}
        nome_cachorro: {type: string, example: Thor}
        raca: {type: string, example: Labrador}
        idade: {type: integer, example: 2}
        nome_completo: {type: string, example: Ana Souza}
        bloco: {type: string, example: B}
        apartamento: {type: string, example: "203"}
  400:
    description: Erro de validação (campos faltando ou idade inválida)
    schema:
      type: object
      properties:
        erro: {type: string, example: "Campos obrigatórios: dono(...) e cachorro(...)"}
"""

    data = request.get_json(force=True, silent=True) or {}

    # Aceita formato aninhado: { dono: {...}, nome_cachorro, raca, idade }
    # ou "achatado": { nome_completo, bloco, apartamento, nome_cachorro, raca, idade }
    dono = data.get("dono") or {}
    nome_completo = (dono.get("nome_completo")
                     or data.get("nome_completo") or "").strip()
    bloco = (dono.get("bloco") or data.get("bloco") or "").strip()
    apartamento = (dono.get("apartamento")
                   or data.get("apartamento") or "").strip()

    nome_cachorro = (data.get("nome_cachorro") or "").strip()
    raca = (data.get("raca") or "").strip()
    idade = data.get("idade")

    # validações
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
        cur = conn.execute(
            "INSERT INTO cachorros(nome_cachorro, raca, idade, dono_id) VALUES (?,?,?,?)",
            (nome_cachorro, raca, idade, dono_id)
        )
        conn.commit()
        novo_id = cur.lastrowid
        row = conn.execute("""
            SELECT c.id, c.nome_cachorro, c.raca, c.idade,
                   d.nome_completo, d.bloco, d.apartamento
            FROM cachorros c
            JOIN donos d ON d.id = c.dono_id
            WHERE c.id = ?
        """, (novo_id,)).fetchone()
        return dict(row), 201


@app.get("/cachorros")
def listar_cachorros():
    """
Listar cachorros
---
tags:
  - Cachorros
summary: Lista todos os cachorros com dados do dono
responses:
  200:
    description: Lista de cachorros
    schema:
      type: array
      items:
        type: object
        properties:
          id: {type: integer, example: 7}
          nome_cachorro: {type: string, example: Thor}
          raca: {type: string, example: Labrador}
          idade: {type: integer, example: 2}
          nome_completo: {type: string, example: Ana Souza}
          bloco: {type: string, example: B}
          apartamento: {type: string, example: "203"}
"""

    with get_conn() as conn:
        rows = conn.execute("""
           SELECT c.id, c.nome_cachorro, c.raca, c.idade,
                  d.nome_completo, d.bloco, d.apartamento
           FROM cachorros c
           JOIN donos d ON d.id = c.dono_id
           ORDER BY c.id DESC
        """).fetchall()
        return [dict(r) for r in rows], 200


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
    required: true
    type: integer
responses:
  200:
    description: Cachorro encontrado
    schema:
      type: object
      properties:
        id: {type: integer, example: 7}
        nome_cachorro: {type: string, example: Thor}
        raca: {type: string, example: Labrador}
        idade: {type: integer, example: 2}
        nome_completo: {type: string, example: Ana Souza}
        bloco: {type: string, example: B}
        apartamento: {type: string, example: "203"}
  404:
    description: Não encontrado
    schema:
      type: object
      properties:
        erro: {type: string, example: "não encontrado"}
"""

    with get_conn() as conn:
        row = conn.execute("""
           SELECT c.id, c.nome_cachorro, c.raca, c.idade,
                  d.nome_completo, d.bloco, d.apartamento
           FROM cachorros c
           JOIN donos d ON d.id = c.dono_id
           WHERE c.id = ?
        """, (cachorro_id,)).fetchone()
        if not row:
            return {"erro": "não encontrado"}, 404
        return dict(row), 200


@app.delete("/cachorros/<int:cachorro_id>")
def deletar_cachorro(cachorro_id):
    """
Deletar cachorro por ID
---
tags:
  - Cachorros
summary: Remove um cachorro específico
description: Exclui definitivamente o registro do cachorro pelo seu identificador.
parameters:
  - in: path
    name: cachorro_id
    required: true
    type: integer
responses:
  204:
    description: Deletado com sucesso (sem corpo na resposta)
  404:
    description: Não encontrado
    schema:
      type: object
      properties:
        erro: {type: string, example: "não encontrado"}
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


if __name__ == "__main__":
    app.run(debug=True)
