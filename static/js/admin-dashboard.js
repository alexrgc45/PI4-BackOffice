import { apiRequest, clearSession } from "./api.js";
import { createCell, formatDate, statusTone } from "./admin-ui.js";

const workRows = document.querySelector("#work-rows");
const receptionList = document.querySelector("#reception-list");
const dashboardStatus = document.querySelector("#dashboard-status");
const logoutButton = document.querySelector("#logout-button");

const completedStates = new Set(["Concluído", "Entregue"]);

logoutButton.addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

document.querySelector("#today-date").textContent = new Intl.DateTimeFormat("pt-PT", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
}).format(new Date());

function setMetric(id, value) {
    document.querySelector(`#${id}`).textContent = String(value);
}

function renderWorks(works) {
    workRows.replaceChildren();
    const activeWorks = works.filter((work) => !completedStates.has(work.estado));
    document.querySelector("#work-count").textContent =
        `${activeWorks.length} ${activeWorks.length === 1 ? "trabalho ativo" : "trabalhos ativos"}`;
    document.querySelector("#work-summary").textContent =
        activeWorks.length === 0 ? "Não há trabalhos ativos por acompanhar." : "Ordenados pelo prazo de entrega mais próximo.";

    if (activeWorks.length === 0) {
        const row = document.createElement("tr");
        const cell = createCell("Não há trabalhos ativos por acompanhar.", "table-placeholder");
        cell.colSpan = 5;
        row.append(cell);
        workRows.append(row);
        return;
    }

    const orderedWorks = [...activeWorks].sort((a, b) => {
        if (!a.data_limite) return 1;
        if (!b.data_limite) return -1;
        return a.data_limite.localeCompare(b.data_limite);
    });

    for (const work of orderedWorks.slice(0, 7)) {
        const row = document.createElement("tr");
        row.append(
            createCell(`#${work.id}`, "work-id"),
            createCell(work.paciente_nome),
            createCell(work.tipo_trabalho_nome || work.natureza),
        );

        const stateCell = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = `status-pill ${statusTone(work.estado)}`;
        badge.textContent = work.estado;
        stateCell.append(badge);
        row.append(stateCell, createCell(formatDate(work.data_limite)));
        workRows.append(row);
    }
}

function renderReception(orders) {
    receptionList.replaceChildren();
    document.querySelector("#reception-summary").textContent =
        orders.length === 0
            ? "Não há pedidos a aguardar análise."
            : `${orders.length} ${orders.length === 1 ? "pedido aguarda" : "pedidos aguardam"} análise.`;

    if (orders.length === 0) {
        const empty = document.createElement("p");
        empty.className = "table-placeholder reception-empty";
        empty.textContent = "A fila de receção está em dia.";
        receptionList.append(empty);
        return;
    }

    for (const order of orders.slice(0, 5)) {
        const item = document.createElement("article");
        item.className = "reception-item";

        const top = document.createElement("div");
        top.className = "reception-item-top";
        const patient = document.createElement("strong");
        patient.textContent = order.paciente_nome;
        const id = document.createElement("span");
        id.textContent = `#${order.id}`;
        top.append(patient, id);

        const detail = document.createElement("p");
        detail.textContent = order.cliente_nome || "Clínica não identificada";
        const date = document.createElement("time");
        date.className = "reception-date";
        date.textContent = formatDate(order.data_criacao?.slice(0, 10));

        item.append(top, detail, date);
        receptionList.append(item);
    }
}

async function loadDashboard() {
    try {
        const [user, works, orders] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/trabalhos/"),
            apiRequest("/api/v1/encomendas/rececao/"),
        ]);

        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        const production = works.filter((work) =>
            ["Por Iniciar", "Em Processamento"].includes(work.estado),
        ).length;
        const standby = works.filter((work) => work.estado === "Em Espera").length;
        const completed = works.filter((work) => completedStates.has(work.estado)).length;

        setMetric("metric-pending", orders.length);
        setMetric("metric-production", production);
        setMetric("metric-standby", standby);
        setMetric("metric-completed", completed);
        renderWorks(works);
        renderReception(orders);
        dashboardStatus.textContent = "Dados atualizados a partir do sistema.";
    } catch (error) {
        dashboardStatus.textContent = error.message || "Não foi possível carregar os dados.";
        dashboardStatus.classList.add("dashboard-status-error");
        workRows.replaceChildren();
        receptionList.replaceChildren();
    }
}

loadDashboard();
