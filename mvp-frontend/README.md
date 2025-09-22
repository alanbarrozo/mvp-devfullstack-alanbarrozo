# Front — Cadastro de Cães do Condomínio (SPA)

Aplicação de página única (HTML/CSS/JS puro) para cadastrar cachorros de um condomínio e exibi-los em **cards com efeito flip**.  
Integra com a **API Flask** (back-end) via `fetch`. Abre direto pelo arquivo `index.html`.

## Principais recursos
- **Formulário “Cadastre seu Pet”** (dono + cachorro)
- **Lista em cards** com **efeito flip 3D** (frente: nome do cão | verso: dados + botões)
- **Detalhes** em **modal** (usa `GET /cachorros/{id}`)
- **Excluir** (usa `DELETE /cachorros/{id}`)
- **Banner** superior **responsivo** com imagem (`banner.png`)
- **Layout responsivo** (celular → desktop → TV)
- **Toasts** de feedback (sucesso/erro)

---

## Pré-requisitos
- Navegador moderno (Chrome/Edge/Firefox/Safari).
- API rodando em `http://127.0.0.1:5000` (ou ajuste a constante `API` no `script.js`).
- CORS habilitado no back (já previsto no projeto).

---

## Como executar (passo a passo)
1. **Suba a API** (back-end):  
   Abra o terminal na pasta do back e rode `python app.py`.  
   Teste em `http://127.0.0.1:5000/status` (deve retornar `{ ok: true, ... }`).

2. **Abra o front**:  
   Dê **duplo clique** no arquivo `index.html` desta pasta (ou use “Open with Live Server”, se preferir).

3. **Use a página**:  
   - Preencha **Nome completo, Bloco, Apartamento, Nome do cachorro, Raça, Idade** → **Cadastrar**.  
   - Passe o **mouse** sobre um card (desktop) ou **toque** (mobile) para virar e ver os botões.  
   - **Detalhes** abre um modal com os dados completos.  
   - **Deletar** remove o registro e atualiza a lista.

> Se sua API estiver em outra URL/porta, **edite** no `script.js`:
```js
const API = 'http://127.0.0.1:5000';

---

## Configurações & Personalização
URL da API

Arquivo: script.js → constante API.

Nome do condomínio

Arquivo: index.html → bloco do banner (.hero-text).
Edite o texto “Condomínio PetLovers”.

Imagem do banner

Substitua o arquivo banner.png (mesmas dimensões aproximadas) ou edite em style.css:

.hero-banner{ background-image: url('banner.png'); }

Altura do banner e tamanhos de fonte

Arquivo: style.css → .hero-banner usa height: clamp(160px, 28vw, 320px);
Ajuste os valores se quiser maior/menor.

Efeito flip dos cards

Estrutura do card (gerada no JS) segue:

<div class="card flip">
  <div class="flip-inner">
    <div class="face flip-front">...</div>
    <div class="face flip-back">...</div>
  </div>
</div>


Regras do flip estão no final do style.css (bloco “FLIP 3D”).
O verso aparece no hover (desktop) ou ao tocar (mobile, via classe .is-flipped).
---

## Rotas da API usadas

POST /cachorros – cria registro (form envia JSON aninhado):

{
  "nome_cachorro": "Thor",
  "raca": "Labrador",
  "idade": 2,
  "dono": { "nome_completo": "Ana Souza", "bloco": "B", "apartamento": "203" }
}


GET /cachorros – lista (usada para renderizar os cards).

GET /cachorros/{id} – detalhes (modal).

DELETE /cachorros/{id} – excluir.

A API também possui GET /donos (lista de donos com quantidade_cachorros) — não é consumida nesta página, mas pode ser usada em uma futura seção “Donos”.

---

## Como testar rapidamente

Abrir http://127.0.0.1:5000/apidocs (Swagger) e validar POST/GET/DELETE.

Abrir index.html, cadastrar 2–3 cães, verificar:

cards aparecem sem recarregar a página,

flip no hover/toque,

Detalhes abre modal com dados do dono,

Deletar remove e atualiza.

Redimensionar a janela (mobile → desktop → TV) para ver a responsividade.

---

## Solução de problemas (FAQ rápido)

“Os cards não aparecem”

Confirme se a API está ativa e GET /cachorros responde.

Veja o Console do navegador (F12 → Console) para erros de JS.

Verifique se a constante API aponta para a URL correta.

“Cadastro não atualiza a lista automaticamente”

Veja se aparece um toast “Cadastro criado!”; se não, há erro na requisição.

Cheque o Console para a mensagem de erro retornada pela API.

“Flip gira, mas só mostra a frente espelhada”

Garanta que o CSS do flip está uma única vez no style.css
(frente/verso com backface-visibility: hidden e transforms nas faces, não no contêiner).

“Banner não aparece”

Confirme a existência de banner.png na mesma pasta do index.html.

Se usar outra imagem, ajuste a URL no style.css.


## Acessibilidade e UX

Banner com role="img" + aria-label.

Toasts com aria-live="polite".

Modal fecha com Esc e pelo botão ×.

Campos com placeholder e validações de entrada.
