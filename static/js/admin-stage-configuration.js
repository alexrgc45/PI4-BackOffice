import { apiRequest, clearSession } from "./api.js";
import { createCell } from "./admin-ui.js";

const typeSelect = document.querySelector("#work-type-select");
const createForm = document.querySelector("#stage-create-form");
const newStageName = document.querySelector("#new-stage-name");
const addStageButton = document.querySelector("#add-stage-button");
const stageRows = document.querySelector("#stage-rows");
const statusMessage = document.querySelector("#stage-status");
const refreshButton = document.querySelector("#refresh-stages");
let workTypes = [];
let stages = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function setStatus(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.classList.toggle("dashboard-status-error", isError);
}

function renderStages() {
    const orderedStages = [...stages].sort(
        (left, right) => left.ordem - right.ordem || left.id - right.id,
    );
    document.querySelector("#stage-count").textContent =
        `${orderedStages.length} ${orderedStages.length === 1 ? "etapa" : "etapas"}`;
    stageRows.replaceChildren();

    if (orderedStages.length === 0) {
        const row = document.createElement("tr");
        const cell = createCell(
            workTypes.length === 0
                ? "Não existem tipos de trabalho configurados."
                : "Este tipo de trabalho ainda não tem etapas.",
            "table-placeholder",
        );
        cell.colSpan = 4;
        row.append(cell);
        stageRows.append(row);
        return;
    }

    orderedStages.forEach((stage, index) => {
        const row = document.createElement("tr");
        const orderCell = document.createElement("td");
        const orderControls = document.createElement("div");
        orderControls.className = "stage-order-controls";
        const orderLabel = document.createElement("span");
        orderLabel.className = "work-id";
        orderLabel.textContent = String(stage.ordem);

        const moveUpButton = document.createElement("button");
        moveUpButton.type = "button";
        moveUpButton.className = "permission-action stage-order-button";
        moveUpButton.dataset.stageId = String(stage.id);
        moveUpButton.dataset.action = "move-up";
        moveUpButton.dataset.boundary = String(index === 0);
        moveUpButton.textContent = "↑";
        moveUpButton.disabled = index === 0;
        moveUpButton.setAttribute("aria-label", `Mover ${stage.nome_etapa} para cima`);

        const moveDownButton = document.createElement("button");
        moveDownButton.type = "button";
        moveDownButton.className = "permission-action stage-order-button";
        moveDownButton.dataset.stageId = String(stage.id);
        moveDownButton.dataset.action = "move-down";
        moveDownButton.dataset.boundary = String(index === orderedStages.length - 1);
        moveDownButton.textContent = "↓";
        moveDownButton.disabled = index === orderedStages.length - 1;
        moveDownButton.setAttribute("aria-label", `Mover ${stage.nome_etapa} para baixo`);
        orderControls.append(orderLabel, moveUpButton, moveDownButton);
        orderCell.append(orderControls);

        const nameCell = document.createElement("td");
        const nameInput = document.createElement("input");
        nameInput.className = "form-control stage-name-input";
        nameInput.type = "text";
        nameInput.maxLength = 150;
        nameInput.value = stage.nome_etapa;
        nameInput.dataset.stageName = String(stage.id);
        nameInput.setAttribute("aria-label", `Nome da etapa ${stage.ordem}`);
        nameCell.append(nameInput);

        const stateCell = document.createElement("td");
        const stateBadge = document.createElement("span");
        stateBadge.className = `status-pill ${stage.ativa ? "status-complete" : "status-inactive"}`;
        stateBadge.textContent = stage.ativa ? "Ativa" : "Inativa";
        stateCell.append(stateBadge);

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "stage-action-group";

        const saveButton = document.createElement("button");
        saveButton.type = "button";
        saveButton.className = "permission-action";
        saveButton.dataset.stageId = String(stage.id);
        saveButton.dataset.action = "save";
        saveButton.textContent = "Guardar nome";
        saveButton.disabled = true;

        const toggleButton = document.createElement("button");
        toggleButton.type = "button";
        toggleButton.className = `permission-action${stage.ativa ? " granted" : ""}`;
        toggleButton.dataset.stageId = String(stage.id);
        toggleButton.dataset.action = "toggle";
        toggleButton.textContent = stage.ativa ? "Desativar" : "Ativar";
        actions.append(saveButton, toggleButton);
        actionsCell.append(actions);
        row.append(orderCell, nameCell, stateCell, actionsCell);
        stageRows.append(row);
    });
}

async function loadStages(typeId, successMessage = "") {
    if (!typeId) {
        stages = [];
        renderStages();
        return;
    }

    setStatus("A carregar etapas…");
    try {
        stages = await apiRequest(`/api/v1/tipos-trabalho/${typeId}/etapas/`);
        renderStages();
        setStatus(successMessage || `${stages.length} ${stages.length === 1 ? "etapa carregada." : "etapas carregadas."}`);
    } catch (error) {
        stages = [];
        renderStages();
        setStatus(error.message || "Não foi possível carregar as etapas.", true);
    }
}

async function loadConfiguration() {
    refreshButton.disabled = true;
    typeSelect.disabled = true;
    addStageButton.disabled = true;
    setStatus("A carregar configuração…");

    try {
        const [user, result] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/tipos-trabalho/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        workTypes = result;
        typeSelect.replaceChildren();

        if (workTypes.length === 0) {
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "Sem tipos de trabalho";
            typeSelect.append(option);
            stages = [];
            renderStages();
            setStatus("Ainda não existem tipos de trabalho configurados.");
            return;
        }

        for (const workType of workTypes) {
            const option = document.createElement("option");
            option.value = String(workType.id);
            option.textContent = workType.ativo ? workType.nome : `${workType.nome} (inativo)`;
            typeSelect.append(option);
        }
        typeSelect.value = String(workTypes[0].id);
        await loadStages(typeSelect.value);
    } catch (error) {
        setStatus(error.message || "Não foi possível carregar a configuração.", true);
        stageRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
        typeSelect.disabled = workTypes.length === 0;
        addStageButton.disabled = workTypes.length === 0;
    }
}

createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const typeId = Number(typeSelect.value);
    const name = newStageName.value.trim();
    if (!Number.isSafeInteger(typeId) || !name) {
        setStatus("Seleciona um tipo de trabalho e indica o nome da etapa.", true);
        return;
    }

    addStageButton.disabled = true;
    setStatus("A adicionar etapa…");
    try {
        await apiRequest(`/api/v1/tipos-trabalho/${typeId}/etapas/`, {
            method: "POST",
            body: { nome_etapa: name },
        });
        newStageName.value = "";
        await loadStages(typeId, "Etapa adicionada aos trabalhos em curso e ao modelo.");
    } catch (error) {
        setStatus(error.message || "Não foi possível adicionar a etapa.", true);
    } finally {
        addStageButton.disabled = false;
    }
});

stageRows.addEventListener("input", (event) => {
    if (!(event.target instanceof HTMLInputElement) || !event.target.matches("[data-stage-name]")) {
        return;
    }
    const row = event.target.closest("tr");
    const stage = stages.find((item) => String(item.id) === event.target.dataset.stageName);
    const saveButton = row.querySelector('button[data-action="save"]');
    const hasUnsavedName = stage && event.target.value.trim() !== stage.nome_etapa;
    saveButton.disabled = !hasUnsavedName;
    for (const button of row.querySelectorAll('button[data-action]:not([data-action="save"])')) {
        button.disabled = Boolean(hasUnsavedName) || button.dataset.boundary === "true";
    }
});

stageRows.addEventListener("click", async (event) => {
    if (!(event.target instanceof Element)) {
        return;
    }
    const button = event.target.closest("button[data-stage-id][data-action]");
    if (!button) {
        return;
    }

    const stageId = Number(button.dataset.stageId);
    const action = button.dataset.action;
    const stage = stages.find((item) => item.id === stageId);
    if (!Number.isSafeInteger(stageId) || !stage) {
        setStatus("Não foi possível identificar a etapa selecionada.", true);
        return;
    }

    let update = {};
    let successMessage = "Etapa atualizada.";
    if (action === "save") {
        const nameInput = stageRows.querySelector(`[data-stage-name="${stageId}"]`);
        const name = nameInput.value.trim();
        if (!name) {
            setStatus("O nome da etapa não pode ficar vazio.", true);
            nameInput.focus();
            return;
        }
        update = { nome_etapa: name };
        successMessage = "Nome da etapa atualizado.";
    } else if (action === "toggle") {
        if (stage.ativa
            && !window.confirm(
                `Desativar "${stage.nome_etapa}" nos trabalhos em curso? Os concluídos não serão alterados.`,
            )) {
            return;
        }
        update = { ativa: !stage.ativa };
        successMessage = stage.ativa ? "Etapa desativada." : "Etapa ativada.";
    } else if (action === "move-up" || action === "move-down") {
        const orderedStages = [...stages].sort(
            (left, right) => left.ordem - right.ordem || left.id - right.id,
        );
        const index = orderedStages.findIndex((item) => item.id === stageId);
        const neighbor = orderedStages[index + (action === "move-up" ? -1 : 1)];
        if (!neighbor) {
            return;
        }
        update = { ordem: neighbor.ordem };
        successMessage = "Ordem das etapas atualizada.";
    } else {
        return;
    }

    for (const rowButton of button.closest("tr").querySelectorAll("button")) {
        rowButton.disabled = true;
    }
    setStatus("A atualizar etapa…");
    try {
        await apiRequest(`/api/v1/etapas-template/${stageId}/`, {
            method: "PATCH",
            body: update,
        });
        await loadStages(typeSelect.value, successMessage);
    } catch (error) {
        setStatus(error.message || "Não foi possível atualizar a etapa.", true);
        const row = button.closest("tr");
        const nameInput = row.querySelector("[data-stage-name]");
        const hasUnsavedName = nameInput.value.trim() !== stage.nome_etapa;
        for (const rowButton of row.querySelectorAll("button[data-action]")) {
            if (rowButton.dataset.action === "save") {
                rowButton.disabled = !hasUnsavedName;
            } else {
                rowButton.disabled = Boolean(hasUnsavedName)
                    || rowButton.dataset.boundary === "true";
            }
        }
    }
});

typeSelect.addEventListener("change", () => loadStages(typeSelect.value));
refreshButton.addEventListener("click", loadConfiguration);

loadConfiguration();
