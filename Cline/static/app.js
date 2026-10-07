const $ = (id) => document.getElementById(id);
const fmt = (n) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n);

let selectedFile = null;

const dropzone = $("upload");
const fileInput = $("fileInput");
const importBtn = $("importBtn");
const importStatus = $("importStatus");
const importDetail = $("importDetail");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) pickFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) pickFile(e.target.files[0]);
});

function pickFile(file) {
  selectedFile = file;
  dropzone.querySelector("span").textContent = file.name;
  importBtn.disabled = false;
  importStatus.textContent = "";
  importDetail.textContent = "";
}

importBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  importBtn.disabled = true;
  importBtn.textContent = "Importando…";
  importStatus.textContent = "";
  importDetail.textContent = "";
  try {
    const form = new FormData();
    form.append("file", selectedFile);
    const res = await fetch("/import", { method: "POST", body: form });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const parts = [];
    parts.push(`importadas: ${data.imported}`);
    parts.push(`duplicatas: ${data.duplicates}`);
    parts.push(`inválidas: ${data.invalid_rows.length}`);
    importStatus.innerHTML = `<span class="pill">${parts.join(" · ")}</span>`;
    if (data.invalid_rows.length) {
      const firstFew = data.invalid_rows.slice(0, 5);
      importDetail.innerHTML =
        `<strong>${data.invalid_rows.length} linha(s) ignorada(s):</strong><br>` +
        firstFew
          .map((r) => `linha ${r.line_number}: ${r.reason}`)
          .join("<br>");
    }
    selectedFile = null;
    dropzone.querySelector("span").textContent = "Clique ou arraste um arquivo CSV";
    importBtn.disabled = true;
    importBtn.textContent = "Importar";
    loadSummary();
    loadTransactions();
  } catch (err) {
    importStatus.textContent = "";
    importDetail.textContent = `Erro: ${err.message}`;
    importBtn.disabled = false;
    importBtn.textContent = "Importar";
  }
});

async function loadSummary() {
  const res = await fetch("/resumo");
  const data = await res.json();
  const saldoEl = $("summaryStats");
  const saldo = data.saldo_total;
  saldoEl.innerHTML = `
    <div class="stat"><div class="label">Saldo total</div>
      <div class="value ${saldo >= 0 ? "positive" : "negative"}">${fmt(saldo)}</div>
    </div>`;
  const tbody = $("catTable").querySelector("tbody");
  tbody.innerHTML = data.totais_por_categoria
    .map(
      (c) =>
        `<tr><td>${c.categoria}</td>
           <td class="amount ${c.total >= 0 ? "positive" : "negative"}">${fmt(c.total)}</td></tr>`
    )
    .join("");
}

async function loadTransactions() {
  const mes = $("monthFilter").value || null;
  const categoria = $("catFilter").value || null;
  const params = new URLSearchParams();
  if (mes) params.set("mes", mes);
  if (categoria) params.set("categoria", categoria);
  const res = await fetch(`/transacoes?${params.toString()}`);
  const rows = await res.json();
  const tbody = $("txTable").querySelector("tbody");
  tbody.innerHTML = rows
    .map((r) => {
      const amountClass = r.amount >= 0 ? "positive" : "negative";
      return `<tr>
        <td>${r.date}</td>
        <td>${r.description}</td>
        <td><span class="pill">${r.categoria}</span></td>
        <td class="amount ${amountClass}">${fmt(r.amount)}</td>
      </tr>`;
    })
    .join("");
  // populate categoria datalist from summary
  const catRes = await fetch("/resumo");
  const catData = await catRes.json();
  const unique = [...new Set(catData.totais_por_categoria.map((c) => c.categoria))];
  const dl = $("catList");
  dl.innerHTML = unique.map((c) => `<option value="${c}">`).join("");
}

$("applyFilters").addEventListener("click", loadTransactions);
$("clearFilters").addEventListener("click", () => {
  $("monthFilter").value = "";
  $("catFilter").value = "";
  loadTransactions();
});

loadSummary();
loadTransactions();
