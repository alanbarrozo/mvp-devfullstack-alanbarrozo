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
            <button data-acao="detalhes" data-id="${c.id}">Detalhes</button>
            <button data-acao="excluir" data-id="${c.id}">Deletar</button>
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

  const html = `
    <p><strong>Cão:</strong> ${c.nome_cachorro} (${c.raca})</p>
    <p><strong>Idade:</strong> ${c.idade}</p>
    <p><strong>Dono:</strong> ${c.nome_completo}</p>
    <p><strong>Bloco/Apto:</strong> ${c.bloco} / ${c.apartamento}</p>
    ${c.created_at_br ? `<p><strong>Desde:</strong> ${c.created_at_br}</p>` : ""}
    ${c.foto_url ? `<img src="${API}${c.foto_url}" alt="Foto do cão" style="max-width:100%;border-radius:12px;margin-top:8px">` : ""}
  `;

  document.querySelector("#modalContent").innerHTML = html;
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
