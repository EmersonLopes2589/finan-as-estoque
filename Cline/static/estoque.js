const $ = (id) => document.getElementById(id);
const money = (n) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n);

const form = $("stockForm");
const nameEl = $("productName");
const qtyEl = $("quantity");
const priceEl = $("unitPrice");
const saveBtn = $("saveBtn");
const toast = $("toast");

function setErr(input, errId, msg) {
  $(errId).textContent = msg || "";
  input.setAttribute("aria-invalid", msg ? "true" : "false");
  return !msg;
}

function validate() {
  let ok = true;
  const name = nameEl.value.trim();
  ok = setErr(nameEl, "errName", name ? "" : "Informe o nome do produto.") && ok;
  const qty = qtyEl.value === "" ? NaN : Number(qtyEl.value);
  ok = setErr(qtyEl, "errQty",
    !Number.isFinite(qty) ? "Digite apenas números." :
    qty < 0 ? "Quantidade deve ser >= 0." : "") && ok;
  const price = priceEl.value === "" ? NaN : Number(priceEl.value);
  ok = setErr(priceEl, "errPrice",
    !Number.isFinite(price) ? "Digite apenas números." :
    price < 0 ? "Preço deve ser >= 0." : "") && ok;
  return ok ? { name, qty, price } : null;
}

[nameEl, qtyEl, priceEl].forEach((el) =>
  el.addEventListener("input", () => setErr(el, el === nameEl ? "errName" : el === qtyEl ? "errQty" : "errPrice", ""))
);

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 4000);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = validate();
  if (!data) return;
  saveBtn.disabled = true;
  saveBtn.textContent = "Salvando…";
  try {
    const res = await fetch("/estoque/itens", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_name: data.name,
        quantity: data.qty,
        unit_price: data.price,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const item = await res.json();
    showToast(`✓ "${item.product_name}" registrado como ${item.product_type}.`);
    form.reset();
    loadGroups();
    loadItems();
  } catch (err) {
    showToast(`Erro: ${err.message}`);
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Registrar item";
  }
});

async function loadGroups() {
  const res = await fetch("/estoque/grupos");
  const groups = await res.json();
  $("groups").innerHTML = groups.length
    ? groups.map((g) =>
        `<div class="chip"><div class="t">${g.product_type}</div>` +
        `<div class="q">${g.items} item(ns) · qtd ${g.total_quantity}</div></div>`).join("")
    : `<span style="color:var(--muted)">Nenhum item ainda.</span>`;
  $("typeList").innerHTML = groups.map((g) => `<option value="${g.product_type}">`).join("");
}

async function loadItems() {
  const tipo = $("typeFilter").value || "";
  const params = new URLSearchParams();
  if (tipo) params.set("tipo", tipo);
  const res = await fetch(`/estoque/itens?${params.toString()}`);
  const rows = await res.json();
  $("itemsTable").querySelector("tbody").innerHTML = rows.map((r) =>
    `<tr><td>${r.product_name}</td>` +
    `<td><span class="badge">${r.product_type}</span></td>` +
    `<td class="num">${r.quantity}</td>` +
    `<td class="num">${money(r.unit_price)}</td>` +
    `<td>${(r.created_at || "").slice(0, 16).replace("T", " ")}</td></tr>`).join("");
}

$("applyFilter").addEventListener("click", loadItems);
$("clearFilter").addEventListener("click", () => {
  $("typeFilter").value = "";
  loadItems();
});

loadGroups();
loadItems();
