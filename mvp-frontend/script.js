// URL base da API
const API = 'http://127.0.0.1:5000';

/* ---------- UI helpers ---------- */
function showToast(msg, tipo = "ok") {
  let box = document.querySelector("#toasts");
  if (!box) {
    box = document.createElement("div");
    box.id = "toasts";
    box.setAttribute("aria-live", "polite");
    box.setAttribute("aria-atomic", "true");
    document.body.appendChild(box);
  }
  const t = document.createElement("div");
  t.className = `toast ${tipo}`;
  t.textContent = msg;
  box.appendChild(t);
  setTimeout(() => t.remove(), 2400);
}

function closeModal() {
  const modal = document.querySelector('#modal');
  if (modal) modal.classList.add('hidden');
}

/* ---------- Renderização de lista ---------- */
async function carregar(q = "") {
  const url = q ? `${API}/cachorros?q=${encodeURIComponent(q)}` : `${API}/cachorros`;
  let dados = [];
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    dados = await res.json();
  } catch (err) {
    console.error('Falha ao carregar lista:', err);
    showToast('Não consegui carregar a lista. Veja o console (F12).', 'err');
    return; // evita tentar montar cards com dados indefinidos
  }

  console.log('GET /cachorros ->', dados.map(d => ({ id: d.id, foto_url: d.foto_url })));

  const cont = document.querySelector('#cards');
  cont.innerHTML = '';

  dados.forEach(c => {
    const card = document.createElement('div');
    card.className = 'card flip';

    // Se tiver imagem, usa <img>; senão, mostra o nome
    const capa = c.foto_url
      ? `<img src="${API}${c.foto_url}" alt="Foto de ${c.nome_cachorro}"
              style="width:100%;height:120px;object-fit:cover;border-radius:10px;">`
      : `<h3 style="margin:0;text-align:center;">${c.nome_cachorro}</h3>
         <small style="display:block;text-align:center;color:#666;margin-top:6px">
           passe o mouse (desktop) ou toque (mobile)
         </small>`;

    card.innerHTML = `
      <div class="flip-inner">
        <div class="face flip-front">
          ${capa}
        </div>
        <div class="face flip-back">
          <h3 style="margin:0 0 6px">${c.nome_cachorro} (${c.raca})</h3>
          <p><strong>Dono:</strong> ${c.nome_completo}</p>
          <p><strong>Bloco/Apto:</strong> ${c.bloco} / ${c.apartamento}</p>
          <p><strong>Idade:</strong> ${c.idade}</p>
          ${c.created_at_br ? `<p style="color:#666"><small>desde: ${c.created_at_br}</small></p>` : ""}
          <div class="row">
            <button class="btn-text"
                    data-acao="detalhes"
                    data-id="${c.id}"
                    title="Ver detalhes">Detalhes</button>

            <button class="btn-icon"
                    data-acao="editar"
                    data-id="${c.id}"
                    aria-label="Editar"
                    title="Editar"
                    data-tooltip="Editar">
              <!-- ícone lápis -->
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1.003 1.003 0 0 0 0-1.41L18.37 3.29a1.003 1.003 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
              </svg>
            </button>

            <button class="btn-icon danger"
                    data-acao="excluir"
                    data-id="${c.id}"
                    aria-label="Excluir"
                    title="Excluir"
                    data-tooltip="Excluir">
              <!-- ícone lixeira -->
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path d="M6 7h12l-1 14H7L6 7zm3-3h6l1 2H8l1-2zM5 7h14v2H5z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    `;

    // flip sem clicar em botão
    card.addEventListener('click', (e) => {
      if (e.target.closest('button')) return;
      card.classList.toggle('is-flipped');
    });

    // ações dos botões
    card.addEventListener('click', async (e) => {
      const btn = e.target.closest('button');
      if (!btn) return;
      const id = btn.dataset.id;
      const acao = btn.dataset.acao;

      if (acao === 'detalhes') await verDetalhes(id);
      if (acao === 'excluir') {
        if (!confirm('Tem certeza que deseja deletar?')) return;
        const del = await fetch(`${API}/cachorros/${id}`, { method: 'DELETE' });
        if (del.ok) { showToast("Excluído!"); carregar(); }
        else {
          const ejson = await del.json().catch(() => ({ erro: "Erro ao excluir" }));
          showToast(ejson.erro || "Erro ao excluir", "err");
        }
      }
    });

    cont.appendChild(card);
  });
}


/* ---------- Detalhes ---------- */
async function verDetalhes(id) {
  const res = await fetch(`${API}/cachorros/${id}`);
  const c = await res.json();

  modalTitle.textContent = `Pet Cadastrado #${id}`;

  const html = `
    <p><strong>Cão:</strong> ${c.nome_cachorro} (${c.raca})</p>
    <p><strong>Idade:</strong> ${c.idade}</p>
    <p><strong>Dono:</strong> ${c.nome_completo}</p>
    <p><strong>Bloco/Apto:</strong> ${c.bloco} / ${c.apartamento}</p>
    ${c.created_at_br ? `<p><strong>Desde:</strong> ${c.created_at_br}</p>` : ""}
    ${c.foto_url ? `<img src="${API}${c.foto_url}" alt="Foto do cão" style="max-width:100%;border-radius:12px;margin-top:8px">` : ""}
  `;

  document.querySelector("#modalContent").innerHTML = html;
  modalContent.classList.remove('hidden');
  formEditar.classList.add('hidden');
  document.querySelector('#modal').classList.remove('hidden');
}

/* ---------- Boot ---------- */
document.addEventListener('DOMContentLoaded', () => {
  const fechar = document.querySelector('#fecharModal');
  if (fechar) fechar.onclick = closeModal;

  // Busca rápida (se tiver input #busca)
  const busca = document.querySelector('#busca');
  let t = null;
  if (busca) {
    busca.addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(() => carregar(busca.value.trim()), 250);
    });
  }

  carregar(); // primeira carga

  const form = document.querySelector('#form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = form.querySelector('button[type="submit"], button');
    if (btn) btn.disabled = true;

    const nome_completo = document.querySelector('#nome_completo').value.trim();
    const bloco = document.querySelector('#bloco').value.trim();
    const apartamento = document.querySelector('#apartamento').value.trim();
    const nome_cachorro = document.querySelector('#nome_cachorro').value.trim();
    const raca = document.querySelector('#raca').value.trim();
    const idade = document.querySelector('#idade').value;

    const body = {
      dono: { nome_completo, bloco, apartamento },
      nome_cachorro, raca, idade
    };

    // 1) Cria o cadastro (JSON)
    const res = await fetch(`${API}/cachorros`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      if (btn) btn.disabled = false;
      const err = await res.json().catch(() => ({ erro: 'Erro' }));
      showToast(err.erro || 'Falha no cadastro', "err");
      return;
    }

    const novo = await res.json();

    // 2) Se o usuário selecionou imagem, envia agora
    const fotoInput = document.querySelector('#foto') || document.querySelector('input[type="file"]');
    const file = fotoInput && fotoInput.files && fotoInput.files[0] ? fotoInput.files[0] : null;

    if (file) {
      const fd = new FormData();
      fd.append('foto', file);
      const up = await fetch(`${API}/cachorros/${novo.id}/foto`, { method: 'POST', body: fd });
      if (!up.ok) {
        const ejson = await up.json().catch(() => ({ erro: "Erro no upload" }));
        showToast(ejson.erro || "Falha no upload da imagem", "err");
      } else {
        showToast("Cadastro + foto enviados!");
      }
    } else {
      showToast("Cadastro criado!");
    }

    // 3) Limpa o form e recarrega a lista
    e.target.reset();
    if (btn) btn.disabled = false;
    carregar();
  });
});

// ---------- EDIÇÃO (abrir modal, preencher, PUT, atualizar) ----------
const modalEl = document.querySelector('#modal');
const modalTitle = document.querySelector('#modalTitle');
const modalContent = document.querySelector('#modalContent');
const formEditar = document.querySelector('#formEditar');

function abrirModal() { modalEl?.classList.remove('hidden'); }
function fecharModal2() { modalEl?.classList.add('hidden'); } // evita conflito de nomes

document.querySelector('#cancelarEdicao')?.addEventListener('click', () => {
  formEditar.classList.add('hidden');
  modalContent.classList.remove('hidden');
  fecharModal2();
});

// Captura cliques no botão "Editar"
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-acao="editar"]');
  if (!btn) return;

  const id = btn.dataset.id;
  try {
    // 1) Busca dados atuais do cachorro (preencher o form)
    const res = await fetch(`${API}/cachorros/${id}`);
    if (!res.ok) throw new Error(`GET /cachorros/${id} -> ${res.status}`);
    const c = await res.json();

    // 2) Prepara o modal em modo edição
    modalTitle.textContent = `Pet Cadastrado #${id}`;
    modalContent.classList.add('hidden');
    formEditar.classList.remove('hidden');

    // 3) Preenche o form
    document.querySelector('#edId').value = id;
    document.querySelector('#edNomeCao').value = c.nome_cachorro ?? '';
    document.querySelector('#edRaca').value = c.raca ?? '';
    document.querySelector('#edIdade').value = c.idade ?? 0;

    document.querySelector('#edNomeDono').value = c.nome_completo ?? '';
    document.querySelector('#edBloco').value = c.bloco ?? '';
    document.querySelector('#edApto').value = c.apartamento ?? '';

    // 4) Abre o modal
    abrirModal();
  } catch (err) {
    console.error(err);
    showToast('Falha ao abrir edição. Veja o console (F12).', 'err');
  }
});

// Submit do form de edição -> PUT /cachorros/:id
formEditar?.addEventListener('submit', async (e) => {
  e.preventDefault();

  const id = document.querySelector('#edId').value;
  const nomeCao = document.querySelector('#edNomeCao').value.trim();
  const raca = document.querySelector('#edRaca').value.trim();
  const idade = document.querySelector('#edIdade').value;

  const nomeDono = document.querySelector('#edNomeDono').value.trim();
  const bloco = document.querySelector('#edBloco').value.trim();
  const apto = document.querySelector('#edApto').value.trim();

  // Monta payload conforme a API (PUT aceita JSON)
  const payload = {
    nome_cachorro: nomeCao,
    raca,
    idade: Number(idade)
  };

  // Regra do backend: só atualiza DONO se vierem os 3 campos juntos
  if (nomeDono || bloco || apto) {
    if (!nomeDono || !bloco || !apto) {
      showToast('Para atualizar o Dono, preencha Nome, Bloco e Apartamento.', 'err');
      return;
    }
    payload.dono = { nome_completo: nomeDono, bloco, apartamento: apto };
  }

  try {
    const res = await fetch(`${API}/cachorros/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const ejson = await res.json().catch(() => ({ erro: 'Erro' }));
      throw new Error(ejson.erro || `PUT falhou (${res.status})`);
    }

    showToast('Atualizado com sucesso!');
    // Fecha o modal e recarrega a lista para refletir as mudanças
    formEditar.classList.add('hidden');
    modalContent.classList.remove('hidden');
    fecharModal2();
    carregar();
  } catch (err) {
    console.error(err);
    showToast(String(err.message || err), 'err');
  }
});
