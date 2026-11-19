import { apiRequest, clearSession } from "./api.js";
import { createCell } from "./admin-ui.js";

const clientRows = document.querySelector("#client-rows");
const searchInput = document.querySelector("#client-search");
const statusFilter = document.querySelector("#client-status");
const statusMessage = document.querySelector("#client-list-status");
const refreshButton = document.querySelector("#refresh-clients");
let clients = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function renderClients() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const selectedStatus = statusFilter.value;
    const filteredClients = clients.filter((client) => {
        const searchableText = [
            client.id,
            client.nome,
            client.nif,
            client.email_contacto,
            client.telefone,
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-PT");
        const matchesStatus = !selectedStatus
            || (selectedStatus === "active" && client.ativo)
            || (selectedStatus === "inactive" && !client.ativo);

        return (!searchTerm || searchableText.includes(searchTerm)) && matchesStatus;
    });

    document.querySelector("#client-count").textContent =
        `${filteredClients.length} de ${clients.length} ${clients.length === 1 ? "cliente" : "clientes"}`;
    statusMessage.textContent = searchTerm || selectedStatus
        ? `${filteredClients.length} resultados encontrados.`
        : `${clients.length} ${clients.length === 1 ? "cliente carregado." : "clientes carregados."}`;
    clientRows.replaceChildren();

    if (filteredClients.length === 0) {
        const row = document.createElement("tr");
        const message = clients.length === 0
            ? "Ainda não existem clientes registados."
            : "Nenhum cliente corresponde aos filtros selecionados.";
        const cell = createCell(message, "table-placeholder");
        cell.colSpan = 6;
        row.append(cell);
        clientRows.append(row);
        return;
    }

    for (const client of filteredClients) {
        const row = document.createElement("tr");
        row.append(
            createCell(client.nome),
            createCell(client.nif),
            createCell(client.email_contacto),
            createCell(client.telefone),
        );

        const accountCell = document.createElement("td");
        const accountBadge = document.createElement("span");
        accountBadge.className = `status-pill ${client.tem_conta ? "status-complete" : "status-waiting"}`;
        accountBadge.textContent = client.tem_conta ? "Com conta" : "Sem conta";
        accountCell.append(accountBadge);

        const statusCell = document.createElement("td");
        const statusBadge = document.createElement("span");
        statusBadge.className = `status-pill ${client.ativo ? "status-complete" : "status-inactive"}`;
        statusBadge.textContent = client.ativo ? "Ativo" : "Inativo";
        statusCell.append(statusBadge);
        row.append(accountCell, statusCell);
        clientRows.append(row);
    }
}

async function loadClients() {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar clientes…";

    try {
        const [user, result] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/clientes/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        clients = result;
        renderClients();
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar os clientes.";
        statusMessage.classList.add("dashboard-status-error");
        clientRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

searchInput.addEventListener("input", renderClients);
statusFilter.addEventListener("change", renderClients);
refreshButton.addEventListener("click", loadClients);

loadClients();
