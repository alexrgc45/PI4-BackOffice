import { apiRequest, clearSession } from "./api.js";
import { createCell, formatDate, statusTone } from "./admin-ui.js";

const completedStates = new Set(["Concluído", "Entregue"]);
const historyRows = document.querySelector("#history-rows");
const searchInput = document.querySelector("#history-search");
const stateFilter = document.querySelector("#history-state");
const statusMessage = document.querySelector("#history-status");
const refreshButton = document.querySelector("#refresh-history");
let historyWorks = [];

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

    const states = [...new Set(historyWorks.map((work) => work.estado).filter(Boolean))]
        .sort((a, b) => a.localeCompare(b, "pt-PT"));
    for (const state of states) {
        const option = document.createElement("option");
        option.value = state;
        option.textContent = state;
        stateFilter.append(option);
    }
}

function renderHistory() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const selectedState = stateFilter.value;
    const filteredWorks = historyWorks.filter((work) => {
        const searchableText = [
            work.id,
            work.paciente_nome,
            work.tipo_trabalho_nome,
            work.natureza,
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-PT");

        return (!searchTerm || searchableText.includes(searchTerm))
            && (!selectedState || work.estado === selectedState);
    }).sort((a, b) => {
        const dateOrder = (b.data_finalizacao || "").localeCompare(a.data_finalizacao || "");
        return dateOrder || b.id - a.id;
    });

    document.querySelector("#history-count").textContent =
        `${filteredWorks.length} de ${historyWorks.length} ${historyWorks.length === 1 ? "trabalho" : "trabalhos"}`;
    statusMessage.textContent = searchTerm || selectedState
        ? `${filteredWorks.length} resultados encontrados.`
        : `${historyWorks.length} ${historyWorks.length === 1 ? "trabalho no histórico." : "trabalhos no histórico."}`;
    historyRows.replaceChildren();

    if (filteredWorks.length === 0) {
        const row = document.createElement("tr");
        const message = historyWorks.length === 0
            ? "Ainda não existem trabalhos concluídos ou entregues."
            : "Nenhum trabalho corresponde aos filtros selecionados.";
        const cell = createCell(message, "table-placeholder");
        cell.colSpan = 5;
        row.append(cell);
        historyRows.append(row);
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
            createCell(formatDate(work.data_finalizacao, "Sem registo")),
        );
        historyRows.append(row);
    }
}

async function loadHistory() {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar histórico…";

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
        historyWorks = result.filter((work) => completedStates.has(work.estado));
        populateStateFilter();
        renderHistory();
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar o histórico.";
        statusMessage.classList.add("dashboard-status-error");
        historyRows.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

searchInput.addEventListener("input", renderHistory);
stateFilter.addEventListener("change", renderHistory);
refreshButton.addEventListener("click", loadHistory);

loadHistory();
