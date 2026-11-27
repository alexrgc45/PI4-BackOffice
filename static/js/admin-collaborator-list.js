import { apiRequest, clearSession } from "./api.js";
import { createCell } from "./admin-ui.js";

const collaboratorRows = document.querySelector("#collaborator-rows");
const searchInput = document.querySelector("#collaborator-search");
const statusFilter = document.querySelector("#collaborator-status-filter");
const statusMessage = document.querySelector("#collaborator-status");
const refreshButton = document.querySelector("#refresh-collaborators");
let collaborators = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function renderCollaborators() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const selectedStatus = statusFilter.value;
    const filteredCollaborators = collaborators.filter((collaborator) => {
        const searchableText = [
            collaborator.id,
            collaborator.nome,
            collaborator.email,
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-PT");
        const matchesStatus = !selectedStatus
            || (selectedStatus === "active" && collaborator.ativo)
            || (selectedStatus === "inactive" && !collaborator.ativo);

        return (!searchTerm || searchableText.includes(searchTerm)) && matchesStatus;
    });

    document.querySelector("#collaborator-count").textContent =
        `${filteredCollaborators.length} de ${collaborators.length} ${collaborators.length === 1 ? "colaborador" : "colaboradores"}`;
    statusMessage.textContent = searchTerm || selectedStatus
        ? `${filteredCollaborators.length} resultados encontrados.`
        : `${collaborators.length} ${collaborators.length === 1 ? "colaborador carregado." : "colaboradores carregados."}`;
    collaboratorRows.replaceChildren();

    if (filteredCollaborators.length === 0) {
        const row = document.createElement("tr");
        const message = collaborators.length === 0
            ? "Ainda não existem colaboradores registados."
            : "Nenhum colaborador corresponde aos filtros selecionados.";
        const cell = createCell(message, "table-placeholder");
        cell.colSpan = 4;
        row.append(cell);
        collaboratorRows.append(row);
        return;
    }

    for (const collaborator of filteredCollaborators) {
        const row = document.createElement("tr");
        row.append(createCell(collaborator.nome), createCell(collaborator.email));

        const statusCell = document.createElement("td");
        const statusBadge = document.createElement("span");
        statusBadge.className = `status-pill ${collaborator.ativo ? "status-complete" : "status-inactive"}`;
        statusBadge.textContent = collaborator.ativo ? "Ativo" : "Inativo";
        statusCell.append(statusBadge);

        const actionCell = document.createElement("td");
        const editLink = document.createElement("a");
        editLink.className = "permission-action";
        editLink.href = `/colaboradores/${encodeURIComponent(String(collaborator.id))}/editar/`;
        editLink.textContent = "Editar";
        editLink.setAttribute("aria-label", `Editar colaborador ${collaborator.nome}`);
        actionCell.append(editLink);

        row.append(statusCell, actionCell);
        collaboratorRows.append(row);
    }
}

async function loadCollaborators(successMessage = "") {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar colaboradores…";

    try {
        const [user, result] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/colaboradores/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        collaborators = result;
        renderCollaborators();
        if (successMessage) {
            statusMessage.textContent = successMessage;
        }
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar os colaboradores.";
        statusMessage.classList.add("dashboard-status-error");
        collaboratorRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

searchInput.addEventListener("input", renderCollaborators);
statusFilter.addEventListener("change", renderCollaborators);
refreshButton.addEventListener("click", () => loadCollaborators());

loadCollaborators();
