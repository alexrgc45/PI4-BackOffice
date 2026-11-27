import { apiRequest, clearSession } from "./api.js";

const form = document.querySelector("#collaborator-edit-form");
const collaboratorId = form.dataset.collaboratorId;
const nameInput = document.querySelector("#collaborator-name");
const emailInput = document.querySelector("#collaborator-email");
const passwordInput = document.querySelector("#collaborator-password");
const statusMessage = document.querySelector("#collaborator-form-status");
const submitButton = document.querySelector("#save-collaborator-button");
const collaboratorListLink = document.querySelector("#collaborator-list-link");

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function setStatus(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.classList.toggle("dashboard-status-error", isError);
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) {
        return;
    }

    submitButton.disabled = true;
    setStatus("A guardar alterações…");

    try {
        await apiRequest(
            `/api/v1/colaboradores/${encodeURIComponent(collaboratorId)}/`,
            {
                method: "PATCH",
                body: {
                    nome: nameInput.value.trim(),
                    email: emailInput.value.trim(),
                    password: passwordInput.value,
                },
            },
        );
        passwordInput.value = "";
        collaboratorListLink.hidden = false;
        setStatus("Colaborador atualizado com sucesso.");
    } catch (error) {
        setStatus(error.message || "Não foi possível guardar o colaborador.", true);
    } finally {
        submitButton.disabled = false;
    }
});

async function loadCollaborator() {
    try {
        const user = await apiRequest("/api/v1/auth/me/");
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        setStatus("A carregar dados do colaborador…");
        const collaborator = await apiRequest(
            `/api/v1/colaboradores/${encodeURIComponent(collaboratorId)}/`,
        );
        nameInput.value = collaborator.nome || "";
        emailInput.value = collaborator.email || "";
        submitButton.disabled = false;
        setStatus("Edite os dados do colaborador.");
    } catch (error) {
        setStatus(error.message || "Não foi possível carregar o colaborador.", true);
    }
}

loadCollaborator();
