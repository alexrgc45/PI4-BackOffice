const ACCESS_TOKEN_KEY = "laboratorio.access";
const REFRESH_TOKEN_KEY = "laboratorio.refresh";

let refreshInProgress;

const legacyRefreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);
if (legacyRefreshToken && !localStorage.getItem(REFRESH_TOKEN_KEY)) {
    localStorage.setItem(REFRESH_TOKEN_KEY, legacyRefreshToken);
}
sessionStorage.removeItem(REFRESH_TOKEN_KEY);

export function saveTokens(tokens) {
    if (typeof tokens.access !== "string" || typeof tokens.refresh !== "string") {
        throw new Error("A resposta de autenticação não contém os tokens esperados.");
    }

    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

export function clearSession() {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function refreshAccessToken() {
    if (!refreshInProgress) {
        refreshInProgress = (async () => {
            const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
            if (!refresh) {
                return null;
            }

            const response = await fetch("/api/v1/auth/token/refresh/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh }),
            });
            if (!response.ok) {
                return null;
            }

            const tokens = await response.json();
            if (typeof tokens.access !== "string") {
                throw new Error("A resposta de renovação não contém um token válido.");
            }
            sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
            return tokens.access;
        })();
    }

    try {
        return await refreshInProgress;
    } finally {
        refreshInProgress = undefined;
    }
}

export async function apiRequest(path, options = {}) {
    const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
    const send = (accessToken) => {
        const headers = new Headers(options.headers || {});
        headers.set("Accept", "application/json");
        if (options.body !== undefined && !isFormData) {
            headers.set("Content-Type", "application/json");
        } else if (isFormData) {
            headers.delete("Content-Type");
        }
        if (accessToken) {
            headers.set("Authorization", `Bearer ${accessToken}`);
        }

        return fetch(path, {
            ...options,
            headers,
            body: options.body === undefined || isFormData
                ? options.body
                : JSON.stringify(options.body),
        });
    };

    let response = await send(sessionStorage.getItem(ACCESS_TOKEN_KEY));
    if (response.status === 401) {
        const refreshedAccess = await refreshAccessToken();
        if (refreshedAccess) {
            response = await send(refreshedAccess);
        }
    }

    if (response.status === 401) {
        clearSession();
        window.location.replace("/");
        throw new Error("A sessão terminou. Inicie sessão novamente.");
    }
    if (!response.ok) {
        const contentType = response.headers.get("content-type") || "";
        if (!contentType.toLowerCase().includes("application/json")) {
            const message = response.status >= 500
                ? "Erro interno do servidor. As alterações não foram guardadas."
                : "O servidor devolveu uma resposta inválida.";
            throw new Error(`${message} (HTTP ${response.status}).`);
        }

        let payload;
        try {
            payload = await response.json();
        } catch {
            throw new Error(
                `O servidor devolveu JSON inválido (HTTP ${response.status}).`,
            );
        }
        const detail = payload?.detail;
        const fieldErrors = payload && typeof payload === "object"
            ? Object.values(payload).flat().find((message) => typeof message === "string")
            : null;
        throw new Error(
            (typeof detail === "string" && detail)
                || fieldErrors
                || "Não foi possível carregar os dados.",
        );
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
}
