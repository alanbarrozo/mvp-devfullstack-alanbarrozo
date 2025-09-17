# 🐾 API — Cadastro de Cães do Condomínio

Este projeto é o **back-end** do MVP desenvolvido para a disciplina de **Desenvolvimento Full Stack Básico (PUC-Rio)**.  
A API foi construída em **Python (Flask)** e utiliza **SQLite** como banco de dados.  
Seu objetivo é permitir o cadastro e gerenciamento de **cães de um condomínio**, incluindo informações de seus donos.

---

## 🚀 Funcionalidades

- ✅ Cadastrar novos cães junto com os dados do dono  
- ✅ Listar todos os cães cadastrados (com informações do dono)  
- ✅ Obter detalhes de um cão específico pelo ID  
- ✅ Deletar um cão pelo ID  
- ✅ Listar donos com a quantidade de cães que cada um possui  
- ✅ Documentação automática com **Swagger (OpenAPI)**  

---

## 🗂 Estrutura do Projeto

backend/
│── app.py # Rotas e lógica da API Flask
│── db.py # Conexão e inicialização do banco SQLite
│── models.sql # Definição do schema do banco de dados
│── mvp.db # Banco de dados SQLite
│── requirements.txt# Dependências do projeto


---

## ⚙️ Instalação e Execução

### 1. Pré-requisitos
- [Python 3.9+](https://www.python.org/downloads/)
- Pip instalado

### 2. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/backend-mvp.git
cd backend-mvp

3. Criar ambiente virtual

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

4. Instalar dependências

pip install -r requirements.txt

5. Inicializar banco de dados

Na primeira execução, o banco será criado automaticamente a partir do models.sql.

6. Rodar a API

python app.py

Por padrão, a API estará disponível em:

http://127.0.0.1:5000

📖 Documentação Swagger

Após iniciar o servidor, acesse:

http://127.0.0.1:5000/apidocs

Lá você encontrará todas as rotas descritas, exemplos de requisições e respostas.

🔗 Endpoints Principais
Método	Rota	Descrição
GET	/status	Verifica status da API
POST	/cachorros	Cadastra novo cachorro + dono
GET	/cachorros	Lista todos os cães cadastrados
GET	/cachorros/<id>	Busca informações de um cão específico
DELETE	/cachorros/<id>	Remove um cão pelo ID
GET	/donos	Lista donos com quantidade de cães
🗄 Banco de Dados

Estrutura definida em models.sql:

donos (id, nome_completo, bloco, apartamento)

cachorros (id, nome_cachorro, raca, idade, dono_id)

Relacionamento:
📌 1 dono → N cachorros

👨‍💻 Tecnologias Utilizadas

Python 3.x

Flask

Flask-CORS

Flasgger (Swagger UI)

SQLite3