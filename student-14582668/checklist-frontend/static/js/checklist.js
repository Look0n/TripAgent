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
