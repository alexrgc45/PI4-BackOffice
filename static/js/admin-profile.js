import { apiRequest, clearSession } from "./api.js";

const profileForm = document.querySelector("#profile-form");
const profileName = document.querySelector("#profile-name");
const profileEmail = document.querySelector("#profile-email");
const profileStatus = document.querySelector("#profile-status");
const saveProfileButton = document.querySelector("#save-profile-button");
const passwordForm = document.querySelector("#password-form");
const passwordStatus = document.querySelector("#password-status");
const changePasswordButton = document.querySelector("#change-password-button");

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function setStatus(element, message, isError = false) {
    element.textContent = message;
    element.classList.toggle("dashboard-status-error", isError);
}

function updateSidebar(profile) {
    document.querySelector("#sidebar-name").textContent = profile.nome;
    document.querySelector("#sidebar-email").textContent = profile.email;
}

async function loadProfile() {
    try {
        const user = await apiRequest("/api/v1/auth/me/");
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        const profile = await apiRequest("/api/v1/admin/perfil/");
        profileName.value = profile.nome;
        profileEmail.value = profile.email;
        updateSidebar(profile);
        setStatus(profileStatus, "Perfil carregado.");
    } catch (error) {
        setStatus(profileStatus, error.message, true);
    }
}

profileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    saveProfileButton.disabled = true;
    setStatus(profileStatus, "A guardar alterações…");

    try {
        const profile = await apiRequest("/api/v1/admin/perfil/", {
            method: "PATCH",
            body: {
                nome: profileName.value.trim(),
                email: profileEmail.value.trim(),
            },
        });
        profileName.value = profile.nome;
        profileEmail.value = profile.email;
        updateSidebar(profile);
        setStatus(profileStatus, "Perfil atualizado com sucesso.");
    } catch (error) {
        setStatus(profileStatus, error.message, true);
    } finally {
        saveProfileButton.disabled = false;
    }
});

passwordForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    changePasswordButton.disabled = true;
    setStatus(passwordStatus, "A atualizar palavra-passe…");

    try {
        const formData = new FormData(passwordForm);
        const response = await apiRequest(
            "/api/v1/admin/perfil/alterar-palavra-passe/",
            {
                method: "POST",
                body: {
                    current_password: formData.get("current_password"),
                    new_password: formData.get("new_password"),
                    confirm_password: formData.get("confirm_password"),
                },
            },
        );
        passwordForm.reset();
        setStatus(passwordStatus, response.detail);
    } catch (error) {
        setStatus(passwordStatus, error.message, true);
    } finally {
        changePasswordButton.disabled = false;
    }
});

loadProfile();
