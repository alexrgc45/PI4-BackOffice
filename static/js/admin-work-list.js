import { apiRequest, clearSession } from "./api.js";
import { createCell, formatDate, statusTone } from "./admin-ui.js";

const workRows = document.querySelector("#work-rows");
const searchInput = document.querySelector("#work-search");
const stateFilter = document.querySelector("#work-state");
const statusMessage = document.querySelector("#work-list-status");
const refreshButton = document.querySelector("#refresh-works");
let works = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function populateStateFilter() {
    stateFilter.replaceChildren();

    const allStates = document.createElement("option");
    allStates.value = "";
    allStates.textContent = "Todos os estados";
    stateFilter.append(allStates);

    const states = [...new Set(works.map((work) => work.estado).filter(Boolean))]
        .sort((a, b) => a.localeCompare(b, "pt-PT"));
    for (const state of states) {
        const option = document.createElement("option");
        option.value = state;
        option.textContent = state;
        stateFilter.append(option);
    }
}

function renderWorks() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const selectedState = stateFilter.value;
    const filteredWorks = works.filter((work) => {
        const searchableText = [
            work.id,
            work.paciente_nome,
            work.tipo_trabalho_nome,
            work.natureza,
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-PT");

        return (!searchTerm || searchableText.includes(searchTerm))
            && (!selectedState || work.estado === selectedState);
    });

    document.querySelector("#work-list-count").textContent =
        `${filteredWorks.length} de ${works.length} ${works.length === 1 ? "trabalho" : "trabalhos"}`;
    statusMessage.textContent = searchTerm || selectedState
        ? `${filteredWorks.length} resultados encontrados.`
        : `${works.length} ${works.length === 1 ? "trabalho carregado." : "trabalhos carregados."}`;
    workRows.replaceChildren();

    if (filteredWorks.length === 0) {
        const row = document.createElement("tr");
        const message = works.length === 0
            ? "Ainda não existem trabalhos registados."
            : "Nenhum trabalho corresponde aos filtros selecionados.";
        const cell = createCell(message, "table-placeholder");
        cell.colSpan = 6;
        row.append(cell);
        workRows.append(row);
        return;
    }

    for (const work of filteredWorks) {
        const row = document.createElement("tr");
        row.append(
            createCell(`#${work.id}`, "work-id"),
            createCell(work.paciente_nome),
            createCell(work.tipo_trabalho_nome || work.natureza),
        );

        const stateCell = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = `status-pill ${statusTone(work.estado)}`;
        badge.textContent = work.estado || "Sem estado";
        stateCell.append(badge);
        row.append(
            stateCell,
            createCell(formatDate(work.data_limite)),
            createCell(formatDate(work.data_proxima_consulta)),
        );
        workRows.append(row);
    }
}

async function loadWorks() {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar trabalhos…";

    try {
        const [user, result] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/trabalhos/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        works = result;
        populateStateFilter();
        renderWorks();
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar os trabalhos.";
        statusMessage.classList.add("dashboard-status-error");
        workRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

searchInput.addEventListener("input", renderWorks);
stateFilter.addEventListener("change", renderWorks);
refreshButton.addEventListener("click", loadWorks);

loadWorks();
