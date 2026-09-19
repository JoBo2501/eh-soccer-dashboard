const root = document.documentElement;
const themeButton = document.querySelector("#theme-toggle");
const refreshButton = document.querySelector("#refresh-data");
let theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
let seasonData;

const $ = (selector) => document.querySelector(selector);
const fmtRecord = (value = "0-0-0") => value.replaceAll("-", "–");
const cleanOpponent = (name = "") => name
  .replace(" University", "")
  .replace(" College", "");
const dateValue = (value) => new Date(`${value}T12:00:00`);
const fmtDate = (value, style = "short") => new Intl.DateTimeFormat("en-US", style === "long"
  ? { month: "short", day: "numeric", year: "numeric" }
  : { month: "short", day: "2-digit" }).format(dateValue(value));

function applyTheme(nextTheme) {
  theme = nextTheme;
  root.dataset.theme = theme;
  themeButton.setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} mode`);
}

function renderNextMatch(match) {
  const node = $("#next-match");
  if (!match) {
    node.innerHTML = `<div class="next-kicker"><i></i> SEASON COMPLETE</div><h2>All fixtures played</h2>`;
    return;
  }
  node.innerHTML = `
    <div class="next-kicker"><i></i> NEXT MATCH${match.conference ? " · SAC" : ""}</div>
    <h2>${match.site === "away" ? "at " : "vs "}${cleanOpponent(match.opponent)}</h2>
    <div class="next-meta"><span>${fmtDate(match.date)} · ${match.time || "TBA"} ET</span><span>${match.site === "home" ? "HOME" : "AWAY"}</span></div>`;
}

function renderPlayer(player, nextMatch) {
  $("#player-stats").innerHTML = [
    [player.minutes, "Minutes"],
    [player.starts, "Starts"],
    [player.appearances, "Verified apps"]
  ].map(([value, label]) => `<div class="player-stat"><strong>${value}</strong><span>${label}</span></div>`).join("");

  const verified = player.verifiedThrough ? `Verified through ${fmtDate(player.verifiedThrough, "long")}` : "Awaiting official match sheets";
  $("#player-next").innerHTML = `
    <p><small>NEXT CHANCE TO WATCH</small><strong>${nextMatch ? `${nextMatch.site === "away" ? "at " : "vs "}${cleanOpponent(nextMatch.opponent)}` : "Season complete"}</strong></p>
    <p><small>OFFICIAL SAMPLE</small><strong>${player.goals} G · ${player.assists} A · ${player.shots} shots · ${player.shotsOnGoal} SOG</strong><small>${verified}</small></p>`;
}

function renderOpponents(matches) {
  const upcoming = matches.filter((match) => match.status !== "final" && match.conference);
  $("#next-opponents").innerHTML = upcoming.slice(0, 3).map((match, index) => `
    <article class="opponent-card">
      <span class="index">0${index + 1}</span>
      <p>${fmtDate(match.date).toUpperCase()} · ${match.site.toUpperCase()}</p>
      <h3>${cleanOpponent(match.opponent)}</h3>
      <div class="opponent-details"><span>${match.location}</span><strong>${match.time || "TBA"} ET</strong></div>
    </article>`).join("");

  $("#fixture-count").textContent = `${upcoming.length} fixtures`;
  $("#fixtures-list").innerHTML = upcoming.map((match, index) => `
    <div class="fixture${index < 3 ? " featured" : ""}">
      <time datetime="${match.date}">${fmtDate(match.date)}</time>
      <span class="venue ${match.site}">${match.site === "home" ? "H" : "A"}</span>
      <strong>${cleanOpponent(match.opponent)}</strong>
      <span>${match.time || "TBA"}</span>
    </div>`).join("");
}

function renderResults(matches) {
  const completed = matches.filter((match) => match.status === "final").sort((a, b) => b.date.localeCompare(a.date));
  $("#results-body").innerHTML = completed.map((match) => `
    <tr data-site="${match.site}">
      <td>${fmtDate(match.date)}</td>
      <td>${cleanOpponent(match.opponent)}${match.conference ? '<small class="conference-tag">SAC</small>' : ""}</td>
      <td>${match.location}</td>
      <td><span class="result-badge ${match.result}">${match.result}</span></td>
      <td class="score">${match.for}–${match.against}</td>
    </tr>`).join("");
}

function renderStandings(standings) {
  $("#standings-body").innerHTML = standings.map((row, index) => `
    <tr class="${row.team.includes("Emory") ? "team-row" : ""}">
      <td>${index + 1}</td>
      <td>${row.team.includes("Emory") ? '<span class="team-dot"></span>' : ""}${row.team}</td>
      <td>${fmtRecord(row.conference)}</td>
      <td>${row.points}</td>
      <td>${fmtRecord(row.overall)}</td>
      <td>${row.form}</td>
    </tr>`).join("");
}

function render(data) {
  seasonData = data;
  const { team, player, matches, standings } = data;
  const nextMatch = matches.find((match) => match.status !== "final");
  const scored = team.games ? team.goalsFor / team.games : 0;
  const conceded = team.games ? team.goalsAgainst / team.games : 0;
  const maxRate = Math.max(scored, conceded, 1);

  $("#overall-record").textContent = fmtRecord(team.overall);
  $("#conference-record").textContent = fmtRecord(team.conference);
  $("#goal-difference").textContent = `${team.goalsFor - team.goalsAgainst >= 0 ? "+" : ""}${team.goalsFor - team.goalsAgainst}`;
  $("#goals-for-average").textContent = scored.toFixed(2);
  $("#goals-against-average").textContent = conceded.toFixed(2);
  $("#shots-average").textContent = (team.shots / team.games).toFixed(1);
  $("#corners-average").textContent = (team.corners / team.games).toFixed(2);
  $("#unbeaten-run").textContent = team.unbeatenRun;
  $("#bar-scored").style.setProperty("--bar", `${Math.max(8, scored / maxRate * 100)}%`);
  $("#bar-conceded").style.setProperty("--bar", `${Math.max(8, conceded / maxRate * 100)}%`);

  renderNextMatch(nextMatch);
  renderPlayer(player, nextMatch);
  renderOpponents(matches);
  renderResults(matches);
  renderStandings(standings);

  const updated = new Date(data.updatedAt);
  const label = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZoneName: "short" }).format(updated);
  $("#rail-updated").textContent = label;
  $("#rail-status").textContent = "Auto-updated";
  $("#source-note").innerHTML = `Updated ${label} from <a href="${data.source}" target="_blank" rel="noreferrer">official SAC data ↗</a>`;
}

async function loadData({ fresh = false } = {}) {
  refreshButton.classList.toggle("refreshing", fresh);
  refreshButton.disabled = true;
  try {
    const response = await fetch(`./data/season.json${fresh ? `?t=${Date.now()}` : ""}`, { cache: fresh ? "no-store" : "default" });
    if (!response.ok) throw new Error(`Data request failed: ${response.status}`);
    render(await response.json());
  } catch (error) {
    $("#rail-status").textContent = "Last saved data";
    $("#source-note").classList.add("data-error");
    $("#source-note").textContent = "Live refresh unavailable. Showing the latest saved season file.";
    console.error(error);
  } finally {
    refreshButton.classList.remove("refreshing");
    refreshButton.disabled = false;
  }
}

applyTheme(theme);
themeButton.addEventListener("click", () => applyTheme(theme === "dark" ? "light" : "dark"));
refreshButton.addEventListener("click", () => loadData({ fresh: true }));

document.querySelectorAll("[data-scroll]").forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById(button.dataset.scroll)?.scrollIntoView({ behavior: "smooth", block: "start" });
    document.querySelectorAll("[data-scroll]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
  });
});

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.querySelectorAll("#results-body tr").forEach((row) => {
      row.hidden = button.dataset.filter !== "all" && row.dataset.site !== button.dataset.filter;
    });
  });
});

loadData();
