const root = document.documentElement;
const themeButton = document.querySelector("#theme-toggle");
let theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

function applyTheme(nextTheme) {
  theme = nextTheme;
  root.setAttribute("data-theme", theme);
  themeButton.setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} mode`);
}

applyTheme(theme);

themeButton.addEventListener("click", () => {
  applyTheme(theme === "dark" ? "light" : "dark");
});

document.querySelectorAll("[data-scroll]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.scroll);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
    document.querySelectorAll("[data-scroll]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
  });
});

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.querySelectorAll("#results-body tr").forEach((row) => {
      row.hidden = filter !== "all" && row.dataset.site !== filter;
    });
  });
});
