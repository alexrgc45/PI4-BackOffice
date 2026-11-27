import { apiRequest, clearSession } from "./api.js";

const clientRows = document.querySelector("#client-rows");
const searchInput = document.querySelector("#client-search");
const statusFilter = document.querySelector("#client-status");
const statusMessage = document.querySelector("#client-list-status");
const clientCount = document.querySelector("#client-count");
const refreshButton = document.querySelector("#refresh-clients");
const clientDetail = document.querySelector("#client-detail");
const clientDoctors = document.querySelector("#client-doctors");
const clientDoctorsCount = document.querySelector("#client-doctors-count");
let clients = [];
let selectedClientId = null;

function formatPhone(value) {
    const digits = String(value || "").replace(/\D/g, "").slice(0, 9);
    return digits.replace(/(\d{3})(?=\d)/g, "$1 ");
}

function makeElement(tagName, className, text) {
    const element = document.createElement(tagName);
    if (className) {
        element.className = className;
    }
    if (text !== undefined) {
        element.textContent = text;
    }
    return element;
}

function initials(name) {
    return String(name || "")
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part.charAt(0))
        .join("")
        .toLocaleUpperCase("pt-PT");
}

function renderClientDetails(client) {
    if (!client) {
        clientDetail.replaceChildren(
            makeElement(
                "p",
                "client-empty-state",
                "Selecione um cliente para consultar os seus dados.",
            ),
        );
        clientDoctorsCount.textContent = "— médicos";
        clientDoctors.replaceChildren(
            makeElement(
                "p",
                "client-empty-state",
                "Selecione um cliente para ver os médicos associados.",
            ),
        );
        return;
    }

    const doctors = Array.isArray(client.medicos_responsaveis)
        ? client.medicos_responsaveis
        : [];
    const header = makeElement("div", "client-detail-header");
    const identity = makeElement("div", "client-detail-identity");
    const state = makeElement(
        "span",
        `status-pill ${client.ativo ? "status-active" : "status-inactive"}`,
        client.ativo ? "ATIVO" : "INATIVO",
    );
    const name = makeElement("h2", "", client.nome || "Cliente");
    const subtitle = makeElement(
        "p",
        "client-detail-subtitle",
        "Cliente e entidade responsável pela faturação",
    );
    identity.append(state, name, subtitle);

    const editLink = makeElement("a", "btn btn-outline-gold client-edit-button", "Editar cliente");
    editLink.href = `/clientes/${encodeURIComponent(String(client.id))}/editar/`;
    header.append(identity, editLink);

    const fields = [
        ["NIF", client.nif],
        ["E-mail", client.email_contacto],
        ["Telefone", formatPhone(client.telefone)],
        ["Médicos associados", doctors.join(", ")],
        ["Conta", client.tem_conta ? "Com conta" : "Sem conta"],
        ["Estado", client.ativo ? "Ativo" : "Inativo"],
    ];
    const detailsGrid = makeElement("div", "client-detail-grid");
    for (const [label, value] of fields) {
        const field = makeElement("div", "client-detail-field");
        field.append(
            makeElement("span", "client-detail-label", label),
            makeElement("strong", "client-detail-value", value || "—"),
        );
        detailsGrid.append(field);
    }
    clientDetail.replaceChildren(header, detailsGrid);

    clientDoctorsCount.textContent =
        `${doctors.length} ${doctors.length === 1 ? "médico" : "médicos"}`;
    if (doctors.length === 0) {
        clientDoctors.replaceChildren(
            makeElement("p", "client-empty-state", "Ainda não existem médicos associados."),
        );
        return;
    }

    const doctorRows = doctors.map((doctor) => {
        const row = makeElement("div", "client-doctor-row");
        const avatar = makeElement("span", "client-avatar", initials(doctor));
        avatar.setAttribute("aria-hidden", "true");
        const description = makeElement("div", "client-doctor-description");
        description.append(
            makeElement("strong", "", doctor),
            makeElement("span", "", "Médico responsável pela clínica"),
        );
        row.append(avatar, description);
        return row;
    });
    clientDoctors.replaceChildren(...doctorRows);
}

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
            formatPhone(client.telefone),
            ...(client.medicos_responsaveis || []),
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-PT");
        const matchesStatus = !selectedStatus
            || (selectedStatus === "active" && client.ativo)
            || (selectedStatus === "inactive" && !client.ativo);

        return (!searchTerm || searchableText.includes(searchTerm)) && matchesStatus;
    });

    clientCount.textContent =
        `${filteredClients.length} ${filteredClients.length === 1 ? "entidade responsável" : "entidades responsáveis"}`;
    statusMessage.textContent = searchTerm || selectedStatus
        ? `${filteredClients.length} resultados encontrados.`
        : `${clients.length} ${clients.length === 1 ? "cliente carregado." : "clientes carregados."}`;
    clientRows.replaceChildren();

    if (filteredClients.length === 0) {
        clientRows.append(
            makeElement(
                "li",
                "client-registry-empty",
                clients.length === 0
                    ? "Ainda não existem clientes registados."
                    : "Nenhum cliente corresponde aos filtros selecionados.",
            ),
        );
        selectedClientId = null;
        renderClientDetails(null);
        return;
    }

    if (!filteredClients.some((client) => String(client.id) === String(selectedClientId))) {
        selectedClientId = filteredClients[0].id;
    }

    for (const client of filteredClients) {
        const listItem = makeElement("li", "client-registry-entry");
        const button = makeElement("button", "client-registry-item");
        button.type = "button";
        button.setAttribute(
            "aria-pressed",
            String(String(client.id) === String(selectedClientId)),
        );
        button.addEventListener("click", () => {
            selectedClientId = client.id;
            for (const item of clientRows.querySelectorAll(".client-registry-item")) {
                item.setAttribute(
                    "aria-pressed",
                    String(item === button),
                );
            }
            renderClientDetails(client);
        });

        const avatar = makeElement("span", "client-avatar", initials(client.nome));
        avatar.setAttribute("aria-hidden", "true");
        const summary = makeElement("span", "client-registry-summary");
        const responsibleDoctors = Array.isArray(client.medicos_responsaveis)
            ? client.medicos_responsaveis
            : [];
        summary.append(
            makeElement("strong", "", client.nome || "Cliente"),
            makeElement(
                "span",
                "",
                `${responsibleDoctors.length} ${responsibleDoctors.length === 1 ? "médico responsável" : "médicos responsáveis"}`,
            ),
        );
        const chevron = makeElement("span", "client-registry-chevron", "›");
        chevron.setAttribute("aria-hidden", "true");
        button.append(avatar, summary, chevron);
        listItem.append(button);
        clientRows.append(listItem);
    }

    const selectedClient = filteredClients.find(
        (client) => String(client.id) === String(selectedClientId),
    );
    renderClientDetails(selectedClient);
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
        selectedClientId = null;
        renderClients();
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar os clientes.";
        statusMessage.classList.add("dashboard-status-error");
        clientCount.textContent = "— entidades responsáveis";
        clientRows.replaceChildren();
        renderClientDetails(null);
    } finally {
        refreshButton.disabled = false;
    }
}

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

searchInput.addEventListener("input", renderClients);
statusFilter.addEventListener("change", renderClients);
refreshButton.addEventListener("click", loadClients);

loadClients();
