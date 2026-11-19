import { apiRequest, clearSession } from "./api.js";
import { createCell } from "./admin-ui.js";

const pendingUserRows = document.querySelector("#pending-user-rows");
const searchInput = document.querySelector("#pending-user-search");
const statusMessage = document.querySelector("#pending-user-status");
const refreshButton = document.querySelector("#refresh-pending-users");
let pendingUsers = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function registrationDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "Data indisponível";
    }

    return new Intl.DateTimeFormat("pt-PT", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(date);
}

function renderPendingUsers() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const filteredUsers = pendingUsers.filter((user) => {
        const searchableText = [user.nome, user.email, user.perfil]
            .filter(Boolean)
            .join(" ")
            .toLocaleLowerCase("pt-PT");
        return !searchTerm || searchableText.includes(searchTerm);
    });

    document.querySelector("#pending-user-count").textContent =
        `${filteredUsers.length} de ${pendingUsers.length} ${pendingUsers.length === 1 ? "pedido" : "pedidos"}`;
    statusMessage.textContent = searchTerm
        ? `${filteredUsers.length} resultados encontrados.`
        : `${pendingUsers.length} ${pendingUsers.length === 1 ? "pedido pendente." : "pedidos pendentes."}`;
    pendingUserRows.replaceChildren();

    if (filteredUsers.length === 0) {
        const row = document.createElement("tr");
        const message = pendingUsers.length === 0
            ? "Não existem pedidos pendentes de aprovação."
            : "Nenhum pedido corresponde à pesquisa.";
        const cell = createCell(message, "table-placeholder");
        cell.colSpan = 5;
        row.append(cell);
        pendingUserRows.append(row);
        return;
    }

    for (const user of filteredUsers) {
        const row = document.createElement("tr");
        row.append(
            createCell(user.nome),
            createCell(user.email),
            createCell(user.perfil),
            createCell(registrationDate(user.criado_em)),
        );

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "pending-user-actions";

        const approveButton = document.createElement("button");
        approveButton.type = "button";
        approveButton.className = "permission-action";
        approveButton.dataset.userId = String(user.id);
        approveButton.dataset.action = "approve";
        approveButton.textContent = "Aceitar";
        approveButton.setAttribute("aria-label", `Aceitar conta de ${user.nome}`);

        const rejectButton = document.createElement("button");
        rejectButton.type = "button";
        rejectButton.className = "permission-action granted";
        rejectButton.dataset.userId = String(user.id);
        rejectButton.dataset.action = "reject";
        rejectButton.textContent = "Rejeitar";
        rejectButton.setAttribute("aria-label", `Rejeitar conta de ${user.nome}`);

        actions.append(approveButton, rejectButton);
        actionsCell.append(actions);
        row.append(actionsCell);
        pendingUserRows.append(row);
    }
}

async function loadPendingUsers(successMessage = "") {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar pedidos…";

    try {
        const [user, result] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/utilizadores/pendentes/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        pendingUsers = result;
        renderPendingUsers();
        if (successMessage) {
            statusMessage.textContent = successMessage;
        }
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar os pedidos.";
        statusMessage.classList.add("dashboard-status-error");
        pendingUserRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

pendingUserRows.addEventListener("click", async (event) => {
    if (!(event.target instanceof Element)) {
        return;
    }
    const button = event.target.closest("button[data-user-id][data-action]");
    if (!button) {
        return;
    }

    const userId = Number(button.dataset.userId);
    const action = button.dataset.action;
    const user = pendingUsers.find((item) => item.id === userId);
    if (!Number.isSafeInteger(userId) || !user || !["approve", "reject"].includes(action)) {
        statusMessage.textContent = "Não foi possível identificar o pedido selecionado.";
        statusMessage.classList.add("dashboard-status-error");
        return;
    }

    if (action === "reject"
        && !window.confirm(`Rejeitar e eliminar o pedido de ${user.nome} (${user.email})?`)) {
        return;
    }

    for (const actionButton of button.closest("tr").querySelectorAll("button")) {
        actionButton.disabled = true;
    }
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = action === "approve"
        ? "A aprovar a conta…"
        : "A rejeitar o pedido…";

    try {
        const endpoint = action === "approve"
            ? `/api/v1/utilizadores/${userId}/aprovar/`
            : `/api/v1/utilizadores/${userId}/rejeitar/`;
        await apiRequest(endpoint, { method: action === "approve" ? "POST" : "DELETE" });
        await loadPendingUsers(
            action === "approve"
                ? "Conta aprovada com sucesso."
                : "Pedido rejeitado e removido.",
        );
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível atualizar o pedido.";
        statusMessage.classList.add("dashboard-status-error");
        for (const actionButton of button.closest("tr").querySelectorAll("button")) {
            actionButton.disabled = false;
        }
    }
});

searchInput.addEventListener("input", renderPendingUsers);
refreshButton.addEventListener("click", () => loadPendingUsers());

loadPendingUsers();
