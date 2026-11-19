import { apiRequest, clearSession } from "./api.js";

const notificationList = document.querySelector("#notification-list");
const searchInput = document.querySelector("#notification-search");
const filterSelect = document.querySelector("#notification-filter");
const statusMessage = document.querySelector("#notification-status");
const refreshButton = document.querySelector("#refresh-notifications");
let notifications = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function formatDateTime(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "Data indisponível";
    }

    return new Intl.DateTimeFormat("pt-PT", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

function getFilteredNotifications() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase("pt-PT");
    const selectedFilter = filterSelect.value;
    return notifications.filter((notification) => {
        const isUnread = !notification.lida_em;
        const matchesFilter = selectedFilter === "all"
            || (selectedFilter === "unread" && isUnread)
            || (selectedFilter === "read" && !isUnread);
        const searchableText = [
            notification.titulo,
            notification.conteudo,
            notification.tipo,
            notification.trabalho,
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-PT");
        return matchesFilter && (!searchTerm || searchableText.includes(searchTerm));
    });
}

function renderNotifications(successMessage = "") {
    const filteredNotifications = getFilteredNotifications();
    const unreadCount = notifications.filter((item) => !item.lida_em).length;
    document.querySelector("#notification-count").textContent = `${unreadCount} por ler`;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = successMessage || (
        filteredNotifications.length === 0
            ? notifications.length === 0
                ? "Não existem notificações."
                : "Não foram encontradas notificações para estes filtros."
            : `${filteredNotifications.length} ${filteredNotifications.length === 1 ? "notificação apresentada." : "notificações apresentadas."}`
    );
    notificationList.replaceChildren();

    if (filteredNotifications.length === 0) {
        const empty = document.createElement("p");
        empty.className = "table-placeholder notification-empty";
        empty.textContent = notifications.length === 0
            ? "A caixa de entrada está vazia."
            : "Altera a pesquisa ou o filtro para ver outras notificações.";
        notificationList.append(empty);
        return;
    }

    for (const notification of filteredNotifications) {
        const card = document.createElement("article");
        card.className = `notification-card${notification.lida_em ? "" : " unread"}`;

        const main = document.createElement("div");
        main.className = "notification-main";

        const heading = document.createElement("div");
        heading.className = "notification-heading";
        const title = document.createElement("h3");
        title.textContent = notification.titulo;
        const type = document.createElement("span");
        type.className = "notification-type";
        type.textContent = notification.tipo.replaceAll("_", " ");
        heading.append(title, type);

        const detail = document.createElement("p");
        detail.className = "notification-content";
        detail.textContent = notification.conteudo || "Sem detalhes adicionais.";

        const metadata = document.createElement("div");
        metadata.className = "notification-metadata";
        const date = document.createElement("time");
        date.dateTime = notification.criada_em;
        date.textContent = formatDateTime(notification.criada_em);
        metadata.append(date);
        if (notification.trabalho) {
            const work = document.createElement("span");
            work.className = "notification-work";
            work.textContent = `Trabalho #${notification.trabalho}`;
            metadata.append(work);
        }
        main.append(heading, detail, metadata);
        card.append(main);

        if (notification.lida_em) {
            const readStatus = document.createElement("span");
            readStatus.className = "status-pill status-complete notification-read-status";
            readStatus.textContent = "Lida";
            card.append(readStatus);
        } else {
            const markReadButton = document.createElement("button");
            markReadButton.type = "button";
            markReadButton.className = "permission-action notification-read-action";
            markReadButton.dataset.notificationId = String(notification.id);
            markReadButton.textContent = "Marcar como lida";
            markReadButton.setAttribute(
                "aria-label",
                `Marcar como lida: ${notification.titulo}`,
            );
            card.append(markReadButton);
        }

        notificationList.append(card);
    }
}

async function loadNotifications() {
    refreshButton.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A carregar notificações…";

    try {
        const [user, result] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/notificacoes/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        notifications = result;
        renderNotifications();
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível carregar as notificações.";
        statusMessage.classList.add("dashboard-status-error");
        notificationList.replaceChildren();
    } finally {
        refreshButton.disabled = false;
    }
}

notificationList.addEventListener("click", async (event) => {
    if (!(event.target instanceof Element)) {
        return;
    }
    const button = event.target.closest("button[data-notification-id]");
    if (!button) {
        return;
    }

    const notificationId = Number(button.dataset.notificationId);
    const notification = notifications.find((item) => item.id === notificationId);
    if (!Number.isSafeInteger(notificationId) || !notification) {
        statusMessage.textContent = "Não foi possível identificar a notificação selecionada.";
        statusMessage.classList.add("dashboard-status-error");
        return;
    }

    button.disabled = true;
    statusMessage.classList.remove("dashboard-status-error");
    statusMessage.textContent = "A atualizar a notificação…";
    try {
        const updatedNotification = await apiRequest(
            `/api/v1/notificacoes/${notificationId}/ler/`,
            { method: "POST" },
        );
        notification.lida_em = updatedNotification.lida_em;
        renderNotifications("Notificação marcada como lida.");
    } catch (error) {
        statusMessage.textContent = error.message || "Não foi possível atualizar a notificação.";
        statusMessage.classList.add("dashboard-status-error");
        button.disabled = false;
    }
});

searchInput.addEventListener("input", () => renderNotifications());
filterSelect.addEventListener("change", () => renderNotifications());
refreshButton.addEventListener("click", loadNotifications);

loadNotifications();
