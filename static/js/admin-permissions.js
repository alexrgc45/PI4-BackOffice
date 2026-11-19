import { apiRequest, clearSession } from "./api.js";
import { createCell } from "./admin-ui.js";

const RECEPTION_PERMISSION = "rececao_trabalhos";
const permissionRows = document.querySelector("#permission-rows");
const searchInput = document.querySelector("#permission-search");
const permissionFilter = document.querySelector("#permission-filter");
const statusMessage = document.querySelector("#permission-status");
const refreshButton = document.querySelector("#refresh-permissions");
let collaborators = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function renderPermissions() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const selectedPermission = permissionFilter.value;
    const filteredCollaborators = collaborators.filter((collaborator) => {
        const searchableText = [collaborator.nome, collaborator.email]
            .filter(Boolean)
            .join(" ")
            .toLocaleLowerCase("pt-PT");
        const hasPermission = collaborator.permissoes.includes(RECEPTION_PERMISSION);
        const matchesPermission = !selectedPermission
            || (selectedPermission === "granted" && hasPermission)
            || (selectedPermission === "not-granted" && !hasPermission);
        return (!searchTerm || searchableText.includes(searchTerm)) && matchesPermission;
    });

    document.querySelector("#permission-count").textContent =
        `${filteredCollaborators.length} de ${collaborators.length} ${collaborators.length === 1 ? "colaborador" : "colaboradores"}`;
    statusMessage.textContent = searchTerm || selectedPermission
        ? `${filteredCollaborators.length} resultados encontrados.`
        : `${collaborators.length} ${collaborators.length === 1 ? "colaborador" : "colaboradores"} consultados.`;
    permissionRows.replaceChildren();

    if (filteredCollaborators.length === 0) {
        const row = document.createElement("tr");
        const message = collaborators.length === 0
            ? "Ainda não existem colaboradores registados."
            : "Nenhum colaborador corresponde aos filtros selecionados.";
        const cell = createCell(message, "table-placeholder");
        cell.colSpan = 5;
        row.append(cell);
        permissionRows.append(row);
        return;
    }

    for (const collaborator of filteredCollaborators) {
        const row = document.createElement("tr");
        row.append(createCell(collaborator.nome), createCell(collaborator.email));

        const accountCell = document.createElement("td");
        const accountStatus = document.createElement("span");
        accountStatus.className = `status-pill ${collaborator.ativo ? "status-complete" : "status-inactive"}`;
        accountStatus.textContent = collaborator.ativo ? "Ativa" : "Inativa";
        accountCell.append(accountStatus);

        const permissionCell = document.createElement("td");
        const permissionStatus = document.createElement("span");
        const hasPermission = collaborator.permissoes.includes(RECEPTION_PERMISSION);
        permissionStatus.className = `status-pill ${hasPermission ? "status-complete" : "status-inactive"}`;
        permissionStatus.textContent = hasPermission ? "Concedida" : "Sem acesso";
        permissionCell.append(permissionStatus);

        const actionCell = document.createElement("td");
        const permissionButton = document.createElement("button");
        permissionButton.type = "button";
        permissionButton.className = `permission-action${hasPermission ? " granted" : ""}`;
        permissionButton.dataset.collaboratorId = String(collaborator.id);
        permissionButton.dataset.granted = String(hasPermission);
        permissionButton.textContent = hasPermission ? "Remover acesso" : "Conceder acesso";
        permissionButton.setAttribute(
            "aria-label",
            `${hasPermission ? "Remover" : "Conceder"} acesso à receção para ${collaborator.nome}`,
        );
        permissionButton.disabled = !collaborator.ativo && !hasPermission;
        actionCell.append(permissionButton);

        row.append(accountCell, permissionCell, actionCell);
        permissionRows.append(row);
    }
}

async function loadPermissions(successMessage = "") {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar permissões…";

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
        renderPermissions();
        if (successMessage) {
            statusMessage.textContent = successMessage;
        }
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar as permissões.";
        statusMessage.classList.add("dashboard-status-error");
        permissionRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

permissionRows.addEventListener("click", async (event) => {
    if (!(event.target instanceof Element)) {
        return;
    }
    const button = event.target.closest("button[data-collaborator-id]");
    if (!button) {
        return;
    }

    const collaboratorId = Number(button.dataset.collaboratorId);
    const hasPermission = button.dataset.granted === "true";
    const collaborator = collaborators.find((item) => item.id === collaboratorId);
    if (!Number.isSafeInteger(collaboratorId) || !collaborator) {
        statusMessage.textContent = "Não foi possível identificar o colaborador selecionado.";
        statusMessage.classList.add("dashboard-status-error");
        return;
    }

    if (hasPermission
        && !window.confirm(`Remover o acesso à receção de trabalhos de ${collaborator.nome}?`)) {
        return;
    }

    button.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A atualizar a permissão…";
    try {
        const permissionUrl = `/api/v1/permissoes/colaboradores/${collaboratorId}/`;
        if (hasPermission) {
            await apiRequest(`${permissionUrl}${RECEPTION_PERMISSION}/`, { method: "DELETE" });
        } else {
            await apiRequest(permissionUrl, {
                method: "POST",
                body: { codigo: RECEPTION_PERMISSION },
            });
        }
        await loadPermissions("Permissão atualizada com sucesso.");
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível atualizar a permissão.";
        statusMessage.classList.add("dashboard-status-error");
        button.disabled = false;
    }
});

searchInput.addEventListener("input", renderPermissions);
permissionFilter.addEventListener("change", renderPermissions);
refreshButton.addEventListener("click", () => loadPermissions());

loadPermissions();
