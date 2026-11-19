import { apiRequest, clearSession, saveTokens } from "./api.js";

const form = document.querySelector("#login-form");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const submitButton = document.querySelector("#login-submit");
const errorMessage = document.querySelector("#login-error");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorMessage.hidden = true;
    submitButton.disabled = true;
    submitButton.textContent = "A autenticar…";

    try {
        const response = await fetch("/api/v1/auth/token/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: emailInput.value.trim(),
                password: passwordInput.value,
            }),
        });
        let tokens;
        try {
            tokens = await response.json();
        } catch {
            throw new Error(
                `O servidor devolveu uma resposta inválida (${response.status}). Verifique a ligação à base de dados.`
            );
        }
        if (!response.ok) {
            throw new Error(tokens.detail || "E-mail ou palavra-passe inválidos.");
        }

        saveTokens(tokens);
        const user = await apiRequest("/api/v1/auth/me/");
        if (user.perfil !== "administrador") {
            clearSession();
            throw new Error("Esta área está disponível apenas para administradores.");
        }

        window.location.replace("/dashboard/");
    } catch (error) {
        errorMessage.textContent = error.message || "Não foi possível iniciar sessão.";
        errorMessage.hidden = false;
        submitButton.disabled = false;
        submitButton.textContent = "Iniciar sessão";
    }
});
