import { apiRequest, clearSession } from "./api.js";
import { createCell, formatDate, statusTone } from "./admin-ui.js";

const receptionRows = document.querySelector("#reception-rows");
const searchInput = document.querySelector("#reception-search");
const statusMessage = document.querySelector("#reception-status");
const refreshButton = document.querySelector("#refresh-reception");
let orders = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function renderOrders() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const filteredOrders = orders.filter((order) => {
        const searchableText = [
            order.id,
            order.paciente_nome,
            order.cliente_nome,
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-PT");
        return !searchTerm || searchableText.includes(searchTerm);
    });

    document.querySelector("#reception-count").textContent =
        `${filteredOrders.length} de ${orders.length} ${orders.length === 1 ? "pedido" : "pedidos"}`;
    statusMessage.textContent = searchTerm
        ? `${filteredOrders.length} resultados encontrados.`
        : `${orders.length} ${orders.length === 1 ? "pedido aguarda análise." : "pedidos aguardam análise."}`;
    receptionRows.replaceChildren();

    if (filteredOrders.length === 0) {
        const row = document.createElement("tr");
        const message = orders.length === 0
            ? "Não existem trabalhos a aguardar receção."
            : "Nenhum pedido corresponde à pesquisa.";
        const cell = createCell(message, "table-placeholder");
        cell.colSpan = 5;
        row.append(cell);
        receptionRows.append(row);
        return;
    }

    for (const order of filteredOrders) {
        const row = document.createElement("tr");
        row.append(
            createCell(`#${order.id}`, "work-id"),
            createCell(order.paciente_nome),
            createCell(order.cliente_nome),
            createCell(formatDate(order.data_criacao?.slice(0, 10), "Sem registo")),
        );

        const stateCell = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = `status-pill ${statusTone(order.estado)}`;
        badge.textContent = order.estado || "Sem estado";
        stateCell.append(badge);
        row.append(stateCell);
        receptionRows.append(row);
    }
}

async function loadReception() {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar pedidos…";

    try {
        const [user, result] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/encomendas/rececao/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        orders = result;
        renderOrders();
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar os pedidos.";
        statusMessage.classList.add("dashboard-status-error");
        receptionRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

searchInput.addEventListener("input", renderOrders);
refreshButton.addEventListener("click", loadReception);

loadReception();
