"use strict";
const $ = (id) => document.getElementById(id);
const viewDescriptions = {
  chat: ["Agent playground", "Talk to the agent and watch every tool action."],
  orders: ["Demo orders", "Browse synthetic orders and track them using MCP."],
  knowledge: ["Knowledge base", "Reference policies that power grounded answers."],
  ticket: ["Ticket tracker", "Look up a demo ticket through the MCP server."]
};
let busy = false;

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function appendMessage(message, kind = "bot", meta = "") {
  const wrapper = node("div", `message ${kind}`);
  wrapper.append(node("div", "avatar", kind === "bot" ? "✳" : "U"));
  const body = node("div", "bubble-wrap");
  body.append(node("div", "who", kind === "bot" ? "SupportDesk Agent" : "You"));
  body.append(node("div", "bubble", message));
  if (meta) body.append(node("div", `message-status ${meta.startsWith("Error") ? "error" : ""}`, meta));
  wrapper.append(body);
  $("messages").append(wrapper);
  $("messages").scrollTop = $("messages").scrollHeight;
}
async function getJson(path) {
  const response = await fetch(path, {cache: "no-store"});
  if (!response.ok) throw new Error(`Unable to load ${path}`);
  return response.json();
}
async function refreshMetrics() {
  try {
    const metrics = await getJson("/api/metrics");
    $("metricRequests").textContent = metrics.requests;
    $("metricSuccess").textContent = `${metrics.success_rate}%`;
    $("metricLatency").textContent = `${metrics.avg_latency_ms}ms`;
    $("metricTickets").textContent = metrics.tickets;
    const list = $("activityList"); list.replaceChildren();
    if (!metrics.recent.length) list.append(node("p", "no-activity", "No activity yet. Ask the agent a question."));
    for (const event of metrics.recent) {
      const line = node("div", "activity-line");
      line.append(node("span", `activity-dot ${event.success ? "" : "fail"}`));
      const description = node("div");
      description.append(node("strong", "", event.tool));
      description.append(node("small", "", `${event.success ? "Completed" : "Failed"} · ${event.latency_ms}ms`));
      line.append(description); list.append(line);
    }
  } catch { $("activityList").replaceChildren(node("p", "no-activity", "Metrics temporarily unavailable")); }
}
function monitor(result, error = false) {
  const status = $("monitorState");
  status.className = `monitor-badge ${error ? "error" : "active"}`;
  status.textContent = error ? "ERROR" : "COMPLETED";
  $("flowPlanner").textContent = error ? "Unable to complete" : `${result.planner} planner`;
  $("flowTool").textContent = error ? "MCP connection error" : result.tool_used;
  $("flowResult").textContent = error ? "Inspect Render logs" : (result.success ? "Grounded answer returned" : "Tool returned no match");
  $("lastTool").textContent = error ? "mcp_connection_error" : result.tool_used;
  $("lastTime").textContent = error ? "Check Render logs for traceback" : `${result.latency_ms}ms · ${result.planner} planner`;
}
async function sendMessage(message) {
  message = message.trim();
  if (!message || busy) return;
  switchView("chat");
  busy = true;
  $("chatSend").disabled = true;
  appendMessage(message, "user");
  $("chatInput").value = "";
  $("monitorState").textContent = "RUNNING";
  $("monitorState").className = "monitor-badge active";
  try {
    const response = await fetch("/api/chat", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Agent request failed");
    appendMessage(data.answer, "bot", `MCP: ${data.tool_used} · ${data.latency_ms}ms · ${data.planner}`);
    monitor(data);
  } catch (err) {
    appendMessage(`I couldn't complete that request. ${err.message}`, "bot", "Error · Please retry");
    monitor(null, true);
  } finally {
    busy = false;
    $("chatSend").disabled = false;
    refreshMetrics();
    $("chatInput").focus();
  }
}
function switchView(view) {
  for (const section of document.querySelectorAll(".view")) section.classList.toggle("is-active", section.id === `view-${view}`);
  for (const button of document.querySelectorAll(".nav-link")) button.classList.toggle("selected", button.dataset.view === view);
  $("breadcrumb").textContent = viewDescriptions[view][0];
  $("panelTitle").textContent = viewDescriptions[view][0];
  $("panelSubtitle").textContent = viewDescriptions[view][1];
}
async function loadOrders() {
  try {
    const data = await getJson("/api/demo/orders");
    const list = $("orderList"); list.replaceChildren();
    for (const order of data.orders) {
      const card = node("div", "item-card"); const info = node("div");
      info.append(node("span", "tag", order.status));
      info.append(node("h4", "", `${order.id} · ${order.product}`));
      info.append(node("p", "", `ETA: ${order.eta} · ${order.detail}`));
      const button = node("button", "", "Track via MCP ↗");
      button.addEventListener("click", () => sendMessage(`Where is order ${order.id}?`));
      card.append(info, button); list.append(card);
    }
  } catch { $("orderList").replaceChildren(node("p", "empty-state", "Orders temporarily unavailable.")); }
}
async function loadKnowledge() {
  try {
    const data = await getJson("/api/knowledge");
    const list = $("articleList"); list.replaceChildren();
    for (const article of data.articles) {
      const card = node("div", "item-card"); const info = node("div");
      info.append(node("h4", "", article.title)); info.append(node("p", "", article.answer));
      const button = node("button", "", "Ask agent ↗");
      button.addEventListener("click", () => sendMessage(`What is your ${article.slug} policy?`));
      card.append(info, button); list.append(card);
    }
  } catch { $("articleList").replaceChildren(node("p", "empty-state", "Knowledge base temporarily unavailable.")); }
}
$("chatForm").addEventListener("submit", (event) => {event.preventDefault(); sendMessage($("chatInput").value);});
$("chatInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); $("chatForm").requestSubmit(); }
});
for (const button of document.querySelectorAll("[data-prompt]")) {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
}
for (const button of document.querySelectorAll("[data-view]")) {
  button.addEventListener("click", () => switchView(button.dataset.view));
}
$("ticketForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const ticket = $("ticketId").value.trim().toUpperCase();
  const email = $("ticketEmail").value.trim();
  sendMessage(`Check ticket status ${ticket} for ${email}`);
});
$("resetChat").addEventListener("click", () => {
  $("messages").replaceChildren();
  appendMessage("New conversation started. How can I help you today?", "bot");
  switchView("chat");
});
$("refreshMetrics").addEventListener("click", refreshMetrics);
refreshMetrics(); loadOrders(); loadKnowledge();
