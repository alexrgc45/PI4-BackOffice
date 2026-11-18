const ACCESS_TOKEN_KEY = "laboratorio.access";
const REFRESH_TOKEN_KEY = "laboratorio.refresh";

let refreshInProgress;

export function saveTokens(tokens) {
    if (typeof tokens.access !== "string" || typeof tokens.refresh !== "string") {
        throw new Error("A resposta de autenticação não contém os tokens esperados.");
    }

    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

export function clearSession() {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function refreshAccessToken() {
    if (!refreshInProgress) {
        refreshInProgress = (async () => {
            const refresh = sessionStorage.getItem(REFRESH_TOKEN_KEY);
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
    const send = (accessToken) => {
        const headers = new Headers(options.headers || {});
        headers.set("Accept", "application/json");
        if (options.body !== undefined) {
            headers.set("Content-Type", "application/json");
        }
        if (accessToken) {
            headers.set("Authorization", `Bearer ${accessToken}`);
        }

        return fetch(path, {
            ...options,
            headers,
            body: options.body === undefined ? undefined : JSON.stringify(options.body),
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
        const payload = await response.json();
        throw new Error(payload.detail || "Não foi possível carregar os dados.");
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
}
