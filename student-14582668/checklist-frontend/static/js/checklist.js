"use strict";

const API_URL = document.body.dataset.apiUrl;

let checklistItems = [];
let activeFilter = "all";
let editingItemId = null;

const itemForm = document.getElementById("item-form");
const itemFormHeading = document.getElementById("item-form-heading");
const saveItemButton = document.getElementById("save-item-button");
const cancelEditButton = document.getElementById("cancel-edit-button");
const checklistContainer = document.getElementById("checklist-items");
const completedCount = document.getElementById("completed-count");
const totalCount = document.getElementById("total-count");
const statusElement = document.getElementById("app-status");
const refreshButton = document.getElementById("refresh-button");
const filterButtons = document.querySelectorAll("[data-filter]");
const aiForm = document.getElementById("ai-form");
const askAiButton = document.getElementById("ask-ai-button");
const aiResults = document.getElementById("ai-results");
const aiReply = document.getElementById("ai-reply");
const aiSuggestions = document.getElementById("ai-suggestions");


class ApiError extends Error {
    constructor(message, status = 0) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}


async function apiRequest(url, options = {}) {
    let response;

    try {
        response = await fetch(url, options);
    } catch (error) {
        throw new ApiError(
            "Unable to connect to the checklist service."
        );
    }

    const responseText = await response.text();
    let payload = {};

    if (responseText) {
        try {
            payload = JSON.parse(responseText);
        } catch (error) {
            throw new ApiError(
                "The checklist service returned an invalid response.",
                response.status
            );
        }
    }

    if (!response.ok) {
        throw new ApiError(
            payload.error || "The request could not be completed.",
            response.status
        );
    }

    return payload;
}


function setStatus(message, type = "info") {
    statusElement.textContent = message;
    statusElement.dataset.type = type;
}


function clearElement(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}


function makeElement(tagName, className, text) {
    const element = document.createElement(tagName);

    if (className) {
        element.className = className;
    }

    if (text !== undefined && text !== null) {
        element.textContent = text;
    }

    return element;
}


function updateSummary() {
    const completed = checklistItems.filter(
        item => Boolean(item.is_completed)
    ).length;

    completedCount.textContent = String(completed);
    totalCount.textContent = String(checklistItems.length);
}


function getVisibleItems() {
    if (activeFilter === "all") {
        return checklistItems;
    }

    return checklistItems.filter(
        item => item.item_type === activeFilter
    );
}


function makeBadge(text, className) {
    return makeElement("span", `badge ${className}`, text);
}


function renderChecklist() {
    clearElement(checklistContainer);
    updateSummary();

    const visibleItems = getVisibleItems();

    if (visibleItems.length === 0) {
        checklistContainer.appendChild(
            makeElement(
                "p",
                "empty-message",
                activeFilter === "all"
                    ? "No checklist items yet."
                    : `No ${activeFilter} items found.`
            )
        );
        return;
    }

    visibleItems.forEach(item => {
        const completed = Boolean(item.is_completed);
        const card = makeElement(
            "article",
            `checklist-card${completed ? " completed" : ""}`
        );
        const mainRow = makeElement("div", "item-main-row");
        const checkbox = document.createElement("input");

        checkbox.type = "checkbox";
        checkbox.checked = completed;
        checkbox.className = "completion-checkbox";
        checkbox.setAttribute(
            "aria-label",
            `${completed ? "Mark incomplete" : "Mark complete"}: ${item.title}`
        );
        checkbox.addEventListener("change", () => {
            updateCompletion(item.item_id, checkbox.checked);
        });

        const content = makeElement("div", "item-content");
        content.appendChild(makeElement("h3", "item-title", item.title));

        const metadata = makeElement("div", "item-metadata");
        metadata.appendChild(
            makeBadge(
                item.item_type === "packing" ? "Packing" : "Task",
                `type-badge type-${item.item_type}`
            )
        );

        if (item.category) {
            metadata.appendChild(
                makeBadge(item.category, "category-badge")
            );
        }

        if (item.priority) {
            metadata.appendChild(
                makeBadge(
                    item.priority,
                    `priority-badge priority-${item.priority.toLowerCase()}`
                )
            );
        }

        content.appendChild(metadata);

        if (item.description) {
            content.appendChild(
                makeElement("p", "item-description", item.description)
            );
        }

        mainRow.appendChild(checkbox);
        mainRow.appendChild(content);
        card.appendChild(mainRow);

        const actions = makeElement("div", "item-actions");
        const editButton = makeElement(
            "button",
            "secondary-button",
            "Edit"
        );
        editButton.type = "button";
        editButton.addEventListener("click", () => beginEdit(item));

        const deleteButton = makeElement(
            "button",
            "danger-button",
            "Delete"
        );
        deleteButton.type = "button";
        deleteButton.addEventListener("click", () => deleteItem(item));

        actions.appendChild(editButton);
        actions.appendChild(deleteButton);
        card.appendChild(actions);
        checklistContainer.appendChild(card);
    });
}


async function loadChecklist(successMessage = "") {
    setStatus("Loading checklist...");
    refreshButton.disabled = true;

    try {
        const items = await apiRequest(API_URL);

        if (!Array.isArray(items)) {
            throw new ApiError(
                "The checklist service returned an invalid item list."
            );
        }

        checklistItems = items;
        renderChecklist();
        setStatus(successMessage || "Checklist loaded.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        refreshButton.disabled = false;
    }
}


function getFormPayload() {
    const formData = new FormData(itemForm);

    return {
        title: formData.get("title").trim(),
        item_type: formData.get("item_type"),
        category: formData.get("category").trim() || null,
        description: formData.get("description").trim() || null,
        priority: formData.get("priority"),
        is_completed: false
    };
}


function resetItemForm() {
    editingItemId = null;
    itemForm.reset();
    document.getElementById("priority").value = "Medium";
    itemFormHeading.textContent = "Add checklist item";
    saveItemButton.textContent = "Save item";
    cancelEditButton.hidden = true;
}


function beginEdit(item) {
    editingItemId = item.item_id;
    document.getElementById("title").value = item.title || "";
    document.getElementById("item-type").value = item.item_type;
    document.getElementById("category").value = item.category || "";
    document.getElementById("description").value = item.description || "";
    document.getElementById("priority").value = item.priority || "Medium";
    itemFormHeading.textContent = "Edit checklist item";
    saveItemButton.textContent = "Update item";
    cancelEditButton.hidden = false;
    itemForm.scrollIntoView({behavior: "smooth", block: "start"});
    document.getElementById("title").focus({preventScroll: true});
}


async function saveItem(event) {
    event.preventDefault();

    const payload = getFormPayload();

    if (!payload.title || !payload.item_type) {
        setStatus("Title and item type are required.", "error");
        return;
    }

    const isEditing = editingItemId !== null;
    const targetUrl = isEditing
        ? `${API_URL}/${editingItemId}`
        : API_URL;

    saveItemButton.disabled = true;
    saveItemButton.textContent = isEditing ? "Updating..." : "Saving...";

    try {
        if (isEditing) {
            delete payload.is_completed;
        }

        await apiRequest(targetUrl, {
            method: isEditing ? "PUT" : "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        resetItemForm();
        await loadChecklist(
            isEditing
                ? "Checklist item updated."
                : "Checklist item added."
        );
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        saveItemButton.disabled = false;
        saveItemButton.textContent = editingItemId !== null
            ? "Update item"
            : "Save item";
    }
}


async function updateCompletion(itemId, isCompleted) {
    setStatus("Updating completion status...");

    try {
        await apiRequest(`${API_URL}/${itemId}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({is_completed: isCompleted})
        });
        await loadChecklist(
            isCompleted ? "Item completed." : "Item marked incomplete."
        );
    } catch (error) {
        await loadChecklist();
        setStatus(error.message, "error");
    }
}


async function deleteItem(item) {
    if (!window.confirm(`Delete "${item.title}"?`)) {
        return;
    }

    setStatus("Deleting checklist item...");

    try {
        await apiRequest(`${API_URL}/${item.item_id}`, {
            method: "DELETE"
        });

        if (editingItemId === item.item_id) {
            resetItemForm();
        }

        await loadChecklist("Checklist item deleted.");
    } catch (error) {
        setStatus(error.message, "error");
    }
}


function selectFilter(filter) {
    activeFilter = filter;

    filterButtons.forEach(button => {
        button.setAttribute(
            "aria-pressed",
            String(button.dataset.filter === activeFilter)
        );
    });

    renderChecklist();
}


async function addSuggestion(suggestion, button) {
    button.disabled = true;
    button.textContent = "Adding...";

    const payload = {
        title: suggestion.title,
        item_type: suggestion.item_type,
        category: suggestion.category || null,
        description: suggestion.description || null,
        priority: suggestion.priority || "Medium",
        is_completed: false
    };

    try {
        await apiRequest(API_URL, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        button.textContent = "Added";
        await loadChecklist("AI suggestion added to the checklist.");
    } catch (error) {
        button.disabled = false;
        button.textContent = "Add to checklist";
        setStatus(error.message, "error");
    }
}


function renderAiSuggestions(suggestions) {
    clearElement(aiSuggestions);

    if (!Array.isArray(suggestions) || suggestions.length === 0) {
        aiSuggestions.appendChild(
            makeElement(
                "p",
                "empty-message",
                "No additional checklist items were suggested."
            )
        );
        return;
    }

    suggestions.forEach(suggestion => {
        const card = makeElement("article", "suggestion-card");
        card.appendChild(
            makeElement("h4", "suggestion-title", suggestion.title)
        );

        const metadata = makeElement("div", "item-metadata");
        metadata.appendChild(
            makeBadge(
                suggestion.item_type === "packing" ? "Packing" : "Task",
                `type-badge type-${suggestion.item_type}`
            )
        );

        if (suggestion.category) {
            metadata.appendChild(
                makeBadge(suggestion.category, "category-badge")
            );
        }

        if (suggestion.priority) {
            metadata.appendChild(
                makeBadge(
                    suggestion.priority,
                    `priority-badge priority-${suggestion.priority.toLowerCase()}`
                )
            );
        }

        card.appendChild(metadata);

        if (suggestion.description) {
            card.appendChild(
                makeElement(
                    "p",
                    "item-description",
                    suggestion.description
                )
            );
        }

        const addButton = makeElement(
            "button",
            "primary-button",
            "Add to checklist"
        );
        addButton.type = "button";
        addButton.addEventListener(
            "click",
            () => addSuggestion(suggestion, addButton)
        );
        card.appendChild(addButton);
        aiSuggestions.appendChild(card);
    });
}


async function requestAiSuggestions(event) {
    event.preventDefault();

    const message = document
        .getElementById("travel-message")
        .value
        .trim();

    if (!message) {
        setStatus("Please describe your trip.", "error");
        return;
    }

    askAiButton.disabled = true;
    askAiButton.textContent = "Getting suggestions...";
    aiResults.hidden = true;
    setStatus("Asking the AI checklist assistant...");

    try {
        const result = await apiRequest(`${API_URL}/recommend`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message})
        });

        aiReply.textContent = result.reply || "Suggestions ready.";
        renderAiSuggestions(result.suggestions);
        aiResults.hidden = false;
        setStatus(
            "AI suggestions are ready. Review them before adding.",
            "success"
        );
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        askAiButton.disabled = false;
        askAiButton.textContent = "Ask AI";
    }
}


itemForm.addEventListener("submit", saveItem);
cancelEditButton.addEventListener("click", resetItemForm);
refreshButton.addEventListener("click", () => loadChecklist());
aiForm.addEventListener("submit", requestAiSuggestions);

filterButtons.forEach(button => {
    button.addEventListener(
        "click",
        () => selectFilter(button.dataset.filter)
    );
});

loadChecklist();

// MCP Connection
const mcpStatus = document.getElementById("mcp-status");
const mcpResults = document.getElementById("mcp-results");
const mcpStatusButton = document.getElementById("mcp-status-button");
const mcpListForm = document.getElementById("mcp-list-form");
const mcpItemForm = document.getElementById("mcp-item-form");
const mcpSummaryButton = document.getElementById("mcp-summary-button");
const mcpActionButtons = document.querySelectorAll("[data-mcp-action]");

let mcpAvailable = false;
let mcpBusy = false;


function updateMcpButtons() {
    mcpStatusButton.disabled = mcpBusy;

    mcpActionButtons.forEach(button => {
        button.disabled = mcpBusy || !mcpAvailable;
    });
}


function setMcpStatus(message, isError = false) {
    mcpStatus.textContent = message;
    mcpStatus.dataset.type = isError ? "error" : "info";
}


async function checkMcpConnection() {
    if (mcpBusy) {
        return;
    }

    mcpBusy = true;
    mcpAvailable = false;
    updateMcpButtons();
    setMcpStatus("Checking MCP connection...");

    try {
        const result = await apiRequest(`${API_URL}/mcp/status`);

        mcpAvailable = result.enabled === true
            && result.available === true;

        if (!result.enabled) {
            setMcpStatus("MCP is disabled in the server configuration.");
        } else if (mcpAvailable) {
            setMcpStatus("MCP connected. Checklist tools are ready.");
        } else {
            setMcpStatus("MCP is unavailable.", true);
        }
    } catch (error) {
        const message = error.status === 401
            ? "Please sign in to use Checklist MCP tools."
            : error.message;

        setMcpStatus(message, true);
    } finally {
        mcpBusy = false;
        updateMcpButtons();
    }
}


function renderMcpItem(item) {
    const card = makeElement("article", "mcp-result-card");

    card.appendChild(
        makeElement("h3", "", `#${item.item_id} ${item.title}`)
    );

    card.appendChild(
        makeElement(
            "p",
            "",
            `${item.item_type} · ${item.priority || "No priority"} · `
            + (item.is_completed ? "Completed" : "Pending")
        )
    );

    if (item.category) {
        card.appendChild(makeElement("p", "", item.category));
    }

    if (item.description) {
        card.appendChild(makeElement("p", "", item.description));
    }

    mcpResults.appendChild(card);
}


function renderMcpResult(toolName, result) {
    clearElement(mcpResults);

    if (toolName === "get_checklist_summary") {
        const summary = result.summary;

        const values = [
            ["Total", summary.total],
            ["Completed", summary.completed],
            ["Pending", summary.pending],
            ["High-priority pending", summary.high_priority_pending],
        ];

        values.forEach(([label, value]) => {
            mcpResults.appendChild(
                makeElement("p", "", `${label}: ${value}`)
            );
        });

        return;
    }

    const items = toolName === "get_checklist_item"
        ? [result.item]
        : result.items;

    if (items.length === 0) {
        mcpResults.appendChild(
            makeElement("p", "", "No matching checklist items.")
        );
        return;
    }

    items.forEach(renderMcpItem);
}


async function runMcpTool(toolName, argumentsObject = {}) {
    if (mcpBusy || !mcpAvailable) {
        return;
    }

    mcpBusy = true;
    updateMcpButtons();
    clearElement(mcpResults);
    setMcpStatus("Running checklist tool...");

    try {
        const response = await apiRequest(`${API_URL}/mcp/call`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                tool: toolName,
                arguments: argumentsObject,
            }),
        });

        if (
            response.success !== true
            || response.result?.success !== true
        ) {
            throw new Error(
                response.error
                || response.result?.error
                || "MCP tool failed."
            );
        }

        renderMcpResult(toolName, response.result);
        setMcpStatus("Checklist tool completed successfully.");
    } catch (error) {
        if ([401, 403, 503].includes(error.status)) {
            mcpAvailable = false;
        }

        clearElement(mcpResults);
        setMcpStatus(error.message, true);
    } finally {
        mcpBusy = false;
        updateMcpButtons();
    }
}


mcpStatusButton.addEventListener("click", checkMcpConnection);

mcpListForm.addEventListener("submit", event => {
    event.preventDefault();

    const argumentsObject = {};
    const itemType = document.getElementById("mcp-item-type").value;
    const priority = document.getElementById("mcp-priority").value;
    const completed = document.getElementById("mcp-completed").value;

    if (itemType) {
        argumentsObject.item_type = itemType;
    }

    if (priority) {
        argumentsObject.priority = priority;
    }

    if (completed !== "") {
        argumentsObject.is_completed = completed === "true";
    }

    runMcpTool("get_checklist_items", argumentsObject);
});

mcpItemForm.addEventListener("submit", event => {
    event.preventDefault();

    const itemId = Number(
        document.getElementById("mcp-item-id").value
    );

    if (!Number.isSafeInteger(itemId) || itemId < 1) {
        setMcpStatus("Enter a positive integer item ID.", true);
        return;
    }

    runMcpTool("get_checklist_item", {item_id: itemId});
});

mcpSummaryButton.addEventListener("click", () => {
    runMcpTool("get_checklist_summary");
});

checkMcpConnection();

const ragStatus = document.getElementById("rag-status");
const ragStatusButton = document.getElementById("rag-status-button");
const ragForm = document.getElementById("rag-form");
const ragQuery = document.getElementById("rag-query");
const ragAskButton = document.getElementById("rag-ask-button");
const ragResults = document.getElementById("rag-results");
const ragAnswer = document.getElementById("rag-answer");
const ragConfidence = document.getElementById("rag-confidence");
const ragCitations = document.getElementById("rag-citations");

let ragAvailable = false;
let ragBusy = false;


function updateRagButtons() {
    ragStatusButton.disabled = ragBusy;
    ragAskButton.disabled = ragBusy || !ragAvailable;
    ragQuery.disabled = ragBusy;
}


function setRagStatus(message, isError = false) {
    ragStatus.textContent = message;
    ragStatus.dataset.type = isError ? "error" : "info";
}


function clearRagResult() {
    ragResults.hidden = true;
    ragAnswer.textContent = "";
    ragConfidence.textContent = "";
    clearElement(ragCitations);
}


async function checkRagConnection() {
    if (ragBusy) {
        return;
    }

    ragBusy = true;
    ragAvailable = false;
    updateRagButtons();
    setRagStatus("Checking RAG connection...");

    try {
        const result = await apiRequest(`${API_URL}/rag/status`);

        ragAvailable = result.enabled === true
            && result.available === true;

        if (result.enabled === false) {
            clearRagResult();
            setRagStatus("RAG mode is disabled.");
        } else if (ragAvailable) {
            setRagStatus("RAG service connected.");
        } else {
            clearRagResult();
            setRagStatus("RAG service is unavailable.", true);
        }
    } catch (error) {
        clearRagResult();
        setRagStatus(
            error.status === 401
                ? "Please log in to use the knowledge assistant."
                : error.message,
            true
        );
    } finally {
        ragBusy = false;
        updateRagButtons();
    }
}


function renderRagAnswer(result) {
    ragAnswer.textContent = result.answer;

    ragConfidence.textContent = (
        `Confidence category: ${result.confidence_category}. `
        + "This is a source-based estimate, not a probability."
    );

    clearElement(ragCitations);

    for (const citation of result.citations) {
        const source = citation.source_id || "Unknown source";
        const chunk = citation.chunk_id || "Unknown chunk";
        const tier = citation.authority_tier || "Unknown tier";

        ragCitations.appendChild(
            makeElement(
                "li",
                "",
                `${source} | ${chunk} | ${tier}`
            )
        );
    }

    if (result.citations.length === 0) {
        ragCitations.appendChild(
            makeElement("li", "", "No sources returned.")
        );
    }

    ragResults.hidden = false;
}


ragStatusButton.addEventListener("click", checkRagConnection);

ragForm.addEventListener("submit", async event => {
    event.preventDefault();

    if (ragBusy || !ragAvailable) {
        return;
    }

    const query = ragQuery.value.trim();

    if (!query) {
        setRagStatus("Enter a question.", true);
        return;
    }

    ragBusy = true;
    updateRagButtons();
    clearRagResult();
    setRagStatus("Retrieving information and generating a response...");

    try {
        const result = await apiRequest(`${API_URL}/rag/answer`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                query,
                k: 5,
            }),
        });

        if (
            result.status !== "success"
            || typeof result.answer !== "string"
            || !Array.isArray(result.citations)
        ) {
            throw new Error(
                result.error || "RAG returned an invalid response."
            );
        }

        renderRagAnswer(result);
        setRagStatus("Response received.");
    } catch (error) {
        if ([401, 403, 503].includes(error.status)) {
            ragAvailable = false;
        }

        clearRagResult();
        setRagStatus(error.message, true);
    } finally {
        ragBusy = false;
        updateRagButtons();
    }
});

checkRagConnection();