const completedStates = new Set(["Concluído", "Entregue"]);

export function formatDate(value) {
    if (!value) {
        return "Sem prazo";
    }

    const date = new Date(`${value}T12:00:00`);
    if (Number.isNaN(date.getTime())) {
        return "Data indisponível";
    }
    return new Intl.DateTimeFormat("pt-PT", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(date);
}

export function statusTone(state) {
    if (completedStates.has(state)) {
        return "status-complete";
    }
    if (state === "Em Espera") {
        return "status-waiting";
    }
    return "status-active";
}

export function createCell(value, className = "") {
    const cell = document.createElement("td");
    cell.textContent = value || "—";
    if (className) {
        cell.className = className;
    }
    return cell;
}
