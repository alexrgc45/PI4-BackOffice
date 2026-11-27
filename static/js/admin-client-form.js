import { apiRequest, clearSession } from "./api.js?v=2";

const form = document.querySelector("#client-create-form");
const clientId = form.dataset.clientId;
const isEditing = Boolean(clientId);
const nameInput = document.querySelector("#client-name");
const nifInput = document.querySelector("#client-nif");
const emailInput = document.querySelector("#client-email");
const passwordInput = document.querySelector("#client-password");
const passwordHint = document.querySelector("#client-password-hint");
const phoneInput = document.querySelector("#client-phone");
const addressInput = document.querySelector("#client-address");
const doctorNameInput = document.querySelector("#doctor-name");
const doctorList = document.querySelector("#doctor-list");
const doctorSummary = document.querySelector("#doctor-summary");
const statusMessage = document.querySelector("#client-form-status");
const submitButton = document.querySelector("#save-client-button");
const clientListLink = document.querySelector("#client-list-link");
const responsibleDoctors = [];

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function setStatus(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.classList.toggle("dashboard-status-error", isError);
}

function formatPhone(value) {
    const digits = String(value || "").replace(/\D/g, "").slice(0, 9);
    return digits.replace(/(\d{3})(?=\d)/g, "$1 ");
}

function formatPhoneInput() {
    const cursor = phoneInput.selectionStart ?? phoneInput.value.length;
    const digitsBeforeCursor = phoneInput.value.slice(0, cursor).replace(/\D/g, "").length;
    phoneInput.value = formatPhone(phoneInput.value);
    const spacesBeforeCursor = digitsBeforeCursor > 0
        ? Math.floor((digitsBeforeCursor - 1) / 3)
        : 0;
    const newCursor = Math.min(
        phoneInput.value.length,
        digitsBeforeCursor + spacesBeforeCursor,
    );
    phoneInput.setSelectionRange(newCursor, newCursor);
}

function renderDoctors() {
    doctorList.replaceChildren();

    responsibleDoctors.forEach((doctor, index) => {
        const chip = document.createElement("span");
        chip.className = "work-create-material-chip";
        const name = document.createElement("span");
        name.textContent = doctor;
        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "×";
        removeButton.setAttribute("aria-label", `Remover ${doctor}`);
        removeButton.addEventListener("click", () => {
            responsibleDoctors.splice(index, 1);
            renderDoctors();
        });
        chip.append(name, removeButton);
        doctorList.append(chip);
    });

    doctorSummary.textContent = responsibleDoctors.length === 0
        ? "Adicione pelo menos um médico responsável."
        : `${responsibleDoctors.length} ${responsibleDoctors.length === 1 ? "médico" : "médicos"} associados.`;
}

function addDoctor() {
    const name = doctorNameInput.value.trim();
    if (!name) {
        setStatus("Indique o nome do médico responsável.", true);
        doctorNameInput.focus();
        return;
    }

    const normalizedName = name.toLocaleLowerCase("pt-PT");
    if (responsibleDoctors.some((doctor) =>
        doctor.toLocaleLowerCase("pt-PT") === normalizedName)) {
        setStatus("Esse médico já foi adicionado.", true);
        doctorNameInput.focus();
        return;
    }

    responsibleDoctors.push(name);
    doctorNameInput.value = "";
    renderDoctors();
    setStatus("Médico responsável adicionado.");
}

function populateClient(client) {
    nameInput.value = client.nome || "";
    nifInput.value = client.nif || "";
    emailInput.value = client.email_contacto || "";
    passwordInput.value = "";
    passwordInput.required = !client.tem_conta;
    passwordInput.placeholder = client.tem_conta
        ? "Deixe vazio para manter"
        : "Mínimo de 8 caracteres";
    passwordHint.textContent = client.tem_conta
        ? "Deixe vazio para manter a password atual."
        : "Este cliente ainda não tem conta. Defina uma password com pelo menos 8 caracteres.";
    phoneInput.value = formatPhone(client.telefone);
    addressInput.value = client.morada || "";
    responsibleDoctors.splice(
        0,
        responsibleDoctors.length,
        ...(Array.isArray(client.medicos_responsaveis) ? client.medicos_responsaveis : []),
    );
    renderDoctors();
}

document.querySelector("#add-doctor").addEventListener("click", addDoctor);
doctorNameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        addDoctor();
    }
});

nifInput.addEventListener("input", () => {
    const cursor = nifInput.selectionStart ?? nifInput.value.length;
    const digitsBeforeCursor = nifInput.value.slice(0, cursor).replace(/\D/g, "").length;
    nifInput.value = nifInput.value.replace(/\D/g, "").slice(0, 9);
    const newCursor = Math.min(digitsBeforeCursor, nifInput.value.length);
    nifInput.setSelectionRange(newCursor, newCursor);
});
phoneInput.addEventListener("input", formatPhoneInput);

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) {
        return;
    }
    if (responsibleDoctors.length === 0) {
        setStatus("Adicione pelo menos um médico responsável.", true);
        doctorNameInput.focus();
        return;
    }

    const phone = phoneInput.value.replace(/\D/g, "");
    if (phone && phone.length !== 9) {
        setStatus("O telefone deve ter exatamente 9 algarismos.", true);
        phoneInput.focus();
        return;
    }

    submitButton.disabled = true;
    setStatus(isEditing ? "A guardar alterações…" : "A criar cliente…");

    try {
        const clientData = Object.fromEntries(new FormData(form).entries());
        clientData.telefone = phone;
        clientData.medicos_responsaveis = [...responsibleDoctors];
        await apiRequest(
            isEditing ? `/api/v1/clientes/${encodeURIComponent(clientId)}/` : "/api/v1/clientes/",
            {
                method: isEditing ? "PATCH" : "POST",
                body: clientData,
            },
        );

        if (!isEditing) {
            form.reset();
            responsibleDoctors.length = 0;
            renderDoctors();
        } else {
            passwordInput.value = "";
        }
        clientListLink.hidden = false;
        setStatus(isEditing ? "Cliente atualizado com sucesso." : "Cliente criado com sucesso.");
    } catch (error) {
        setStatus(error.message || "Não foi possível guardar o cliente.", true);
    } finally {
        submitButton.disabled = false;
    }
});

async function loadCurrentUser() {
    try {
        const user = await apiRequest("/api/v1/auth/me/");
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        if (isEditing) {
            setStatus("A carregar dados do cliente…");
            const client = await apiRequest(`/api/v1/clientes/${encodeURIComponent(clientId)}/`);
            populateClient(client);
        }

        submitButton.disabled = false;
        setStatus(isEditing ? "Edite os dados do cliente." : "Preencha os dados do cliente.");
    } catch (error) {
        setStatus(error.message || "Não foi possível carregar o cliente.", true);
    }
}

loadCurrentUser();
