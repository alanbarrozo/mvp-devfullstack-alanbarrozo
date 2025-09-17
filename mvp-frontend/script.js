const API = 'http://127.0.0.1:5000';

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

function openModal(html) {
  document.querySelector("#modalContent").innerHTML = html;
  document.querySelector("#modal").classList.remove("hidden");
}
function closeModal() {
  document.querySelector("#modal").classList.add("hidden");
}
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

async function verDetalhes(id) {
  openModal("<p>Carregando...</p>");
  const r = await fetch(`${API}/cachorros/${id}`);
  if (!r.ok) { openModal("<p>Não encontrado.</p>"); return; }
  const c = await r.json();
  openModal(`
    <p><strong>Cão:</strong> ${c.nome_cachorro}</p>
    <p><strong>Raça:</strong> ${c.raca}</p>
    <p><strong>Idade:</strong> ${c.idade}</p>
    <hr>
    <p><strong>Dono:</strong> ${c.nome_completo}</p>
    <p><strong>Bloco/Apto:</strong> ${c.bloco} / ${c.apartamento}</p>
  `);
}


async function carregar() {
  const res = await fetch(`${API}/cachorros`);
  const dados = await res.json();

  const cont = document.querySelector('#cards');
  cont.innerHTML = '';

  dados.forEach(c => {
    const card = document.createElement('div');
    card.className = 'card flip';
    card.innerHTML = `
  <div class="flip-inner">
    <div class="face flip-front">
      <h3 style="margin:0;text-align:center;">${c.nome_cachorro}</h3>
      <small style="display:block;text-align:center;color:#666;margin-top:6px">
        passe o mouse (desktop) ou toque (mobile)
      </small>
    </div>
    <div class="face flip-back">
      <h3 style="margin:0 0 6px">${c.nome_cachorro} (${c.raca})</h3>
      <p><strong>Dono:</strong> ${c.nome_completo}</p>
      <p><strong>Bloco/Apto:</strong> ${c.bloco} / ${c.apartamento}</p>
      <p><strong>Idade:</strong> ${c.idade}</p>
      <div class="row">
        <button data-acao="detalhes" data-id="${c.id}">Detalhes</button>
        <button data-acao="excluir" data-id="${c.id}">Deletar</button>
      </div>
    </div>
  </div>
`;

    cont.appendChild(card);
    // toggle para mobile: tocar no card alterna o flip (exceto quando clicar em botão)
    card.addEventListener('click', (e) => {
      if (e.target.closest('button')) return; // não interferir nos botões
      card.classList.toggle('is-flipped');
    });

  });

  // ações dos botões (detalhes / excluir)
  cont.querySelectorAll('button[data-acao]').forEach(btn => {
    const id = btn.dataset.id;
    if (btn.dataset.acao === "detalhes") {
      btn.onclick = () => verDetalhes(id);
    } else {
      btn.onclick = async () => {
        if (!confirm('Excluir este cadastro?')) return;
        const r = await fetch(`${API}/cachorros/${id}`, { method: 'DELETE' });
        if (r.status === 204) { showToast("Excluído"); carregar(); }
        else showToast('Erro ao excluir', 'err');
      };
    }
  });
}


document.addEventListener('DOMContentLoaded', () => {
  // só agora o HTML existe (inclui #fecharModal, #form, #cards)
  const fechar = document.querySelector('#fecharModal');
  if (fechar) fechar.onclick = closeModal;

  carregar();

  const form = document.querySelector('#form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = e.submitter || e.target.querySelector('button');

    // DONO
    const nome_completo = document.querySelector('#nome_completo').value.trim();
    const bloco = document.querySelector('#bloco').value.trim();
    const apartamento = document.querySelector('#apartamento').value.trim();

    // CACHORRO
    const nome_cachorro = document.querySelector('#nome_cachorro').value.trim();
    const raca = document.querySelector('#raca').value.trim();
    const idadeVal = document.querySelector('#idade').value;
    const idade = Number.parseInt(idadeVal, 10);

    // validações simples
    if (!nome_completo || !bloco || !apartamento || !nome_cachorro || !raca) {
      showToast("Preencha todos os campos.", "err"); return;
    }
    if (Number.isNaN(idade) || idade < 0) {
      showToast("Idade deve ser número inteiro ≥ 0.", "err"); return;
    }

    // JSON no formato novo (aninhado)
    const body = {
      nome_cachorro, raca, idade,
      dono: { nome_completo, bloco, apartamento }
    };

    btn.disabled = true;
    const res = await fetch(`${API}/cachorros`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    btn.disabled = false;

    if (res.ok) {
      e.target.reset();
      showToast("Cadastro criado!");
      carregar(); // atualiza a lista
    } else {
      const err = await res.json().catch(() => ({ erro: 'Erro' }));
      showToast(err.erro || 'Falha no cadastro', "err");
    }
  });
});
