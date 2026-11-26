const themeToggle = document.querySelector("#theme-toggle");
const themeToggleLabel = document.querySelector("#theme-toggle-label");
const themeToggleIcon = document.querySelector(".theme-toggle-icon");

function updateThemeToggle(theme) {
    const isLight = theme === "light";
    themeToggleLabel.textContent = isLight ? "Modo escuro" : "Modo claro";
    themeToggleIcon.textContent = isLight ? "◐" : "☼";
    themeToggle.setAttribute(
        "aria-label",
        isLight ? "Ativar modo escuro" : "Ativar modo claro"
    );
}

updateThemeToggle(document.documentElement.dataset.theme);

themeToggle.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem("backoffice-theme", nextTheme);
    updateThemeToggle(nextTheme);
});
