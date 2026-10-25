"use strict";

const MULTI_AGENT_URL = `${API_URL}/multi-agent`;
const MULTI_AGENT_WAIT_MS = 16 * 60 * 1000;

const multiAgentForm = document.getElementById("multi-agent-form");
const multiAgentRequest = document.getElementById("multi-agent-request");
const multiAgentStart = document.getElementById("multi-agent-start");
const multiAgentConnection = document.getElementById("multi-agent-connection");
const multiAgentToggle = document.getElementById("multi-agent-toggle");
const multiAgentStatus = document.getElementById("multi-agent-status");
const multiAgentResults = document.getElementById("multi-agent-results");
const multiAgentRefresh = document.getElementById("multi-agent-refresh");
const multiAgentReviewForm = document.getElementById("multi-agent-review-form");
const multiAgentReviewFields = document.getElementById("multi-agent-review-fields");
const multiAgentCorrection = document.getElementById("multi-agent-correction");

let multiAgentAvailable = false;
let multiAgentEnabled = false;
let multiAgentLocked = false;
let multiAgentModeKnown = false;
let multiAgentBusy = false;
let multiAgentWorkflow = null;
let multiAgentTimer = null;
let multiAgentDeadline = 0;


function setMultiAgentStatus(message) {
    multiAgentStatus.textContent = message;
}


function updateMultiAgentButtons() {
    const status = multiAgentWorkflow?.status;

    const active = [
        "queued",
        "running",
        "pending_review"
    ].includes(status);

    multiAgentStart.disabled =
        !multiAgentAvailable || multiAgentBusy || active;

    multiAgentConnection.disabled = multiAgentBusy;
    multiAgentToggle.disabled = multiAgentBusy || !multiAgentModeKnown || multiAgentLocked;
    multiAgentToggle.textContent = `Multi-Agent: ${multiAgentEnabled ? "ON" : "OFF"}`;
    multiAgentToggle.setAttribute("aria-pressed", String(multiAgentEnabled));
    multiAgentToggle.title = multiAgentLocked
        ? "Multi-Agent mode is locked by the administrator."
        : "Turn Checklist Multi-Agent mode on or off.";

    multiAgentRefresh.disabled =
        !multiAgentEnabled || multiAgentBusy || !multiAgentWorkflow;

    multiAgentReviewFields.disabled =
        !multiAgentEnabled || multiAgentBusy || status !== "pending_review";
}


function stopMultiAgentPolling() {
    window.clearTimeout(multiAgentTimer);
    multiAgentTimer = null;
}


function renderMultiAgentWorkflow(workflow) {
    multiAgentWorkflow = workflow;
    multiAgentResults.hidden = false;

    document.getElementById("multi-agent-workflow-id").textContent =
        `Workflow: ${workflow.workflow_id}`;

    document.getElementById("multi-agent-plan").textContent =
        workflow.planner_result?.plan || "Waiting for Planner.";

    document.getElementById("multi-agent-output").textContent =
        workflow.worker_result?.output || "Waiting for Worker.";

    document.getElementById("multi-agent-review").textContent =
        workflow.reviewer_result?.review || "Waiting for Reviewer.";

    document.getElementById("multi-agent-evidence").textContent =
        JSON.stringify(workflow.worker_result?.evidence || [], null, 2);

    const decision = workflow.human_decision;

    document.getElementById("multi-agent-decision").textContent =
        decision?.status === "completed"
            ? `Decision: ${decision.decision}. ${decision.correction || ""}`
            : "No human decision recorded.";

    setMultiAgentStatus(
        workflow.status === "failed"
            ? `Workflow failed: ${workflow.error || "Unknown error"}`
            : `Workflow status: ${workflow.status}`
    );

    updateMultiAgentButtons();
}


function scheduleMultiAgentPoll() {
    stopMultiAgentPolling();

    if (!multiAgentEnabled || !["queued", "running"].includes(multiAgentWorkflow?.status)) {
        return;
    }

    if (Date.now() >= multiAgentDeadline) {
        setMultiAgentStatus(
            "Automatic checking stopped. Use Refresh workflow to check again. " +
            "The server task has not been cancelled."
        );
        return;
    }

    multiAgentTimer = window.setTimeout(
        refreshMultiAgentWorkflow,
        2000
    );
}


async function checkMultiAgentConnection() {
    if (multiAgentBusy) {
        return;
    }

    multiAgentBusy = true;
    updateMultiAgentButtons();

    try {
        const mode = await apiRequest(`${MULTI_AGENT_URL}/mode`);
        applyMultiAgentMode(mode);

        if (!multiAgentEnabled) {
            showMultiAgentOff();
            return;
        }

        const result = await apiRequest(
            `${MULTI_AGENT_URL}/status`
        );

        multiAgentAvailable =
            result.enabled === true && result.available === true;

        setMultiAgentStatus(
            multiAgentAvailable
                ? "Multi-Agent server is available."
                : "Multi-Agent mode is disabled or unavailable."
        );
    } catch (error) {
        multiAgentAvailable = false;
        setMultiAgentStatus(error.message);
    } finally {
        multiAgentBusy = false;
        updateMultiAgentButtons();
    }
}


function applyMultiAgentMode(mode) {
    multiAgentEnabled = mode.enabled === true;
    multiAgentLocked = mode.locked === true;
    multiAgentModeKnown = true;
    multiAgentAvailable = false;

    if (!multiAgentEnabled) {
        stopMultiAgentPolling();
    }
}


function showMultiAgentOff() {
    setMultiAgentStatus(
        multiAgentLocked
            ? "Multi-Agent mode is OFF and locked by the administrator."
            : "Multi-Agent mode is OFF. Turn it ON to start a review. " +
              "Switching OFF does not cancel a workflow already running on the server."
    );
}


async function toggleMultiAgentMode() {
    if (multiAgentBusy || !multiAgentModeKnown || multiAgentLocked) {
        return;
    }

    stopMultiAgentPolling();
    multiAgentBusy = true;
    updateMultiAgentButtons();
    let succeeded = false;

    try {
        const mode = await apiRequest(`${MULTI_AGENT_URL}/mode`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({enabled: !multiAgentEnabled})
        });
        applyMultiAgentMode(mode);
        succeeded = true;
        if (!multiAgentEnabled) {
            showMultiAgentOff();
        }
    } catch (error) {
        setMultiAgentStatus(`${error.message} Use Check connection to refresh the mode.`);
    } finally {
        multiAgentBusy = false;
        updateMultiAgentButtons();
    }

    if (succeeded && multiAgentEnabled) {
        await checkMultiAgentConnection();
        if (multiAgentAvailable && multiAgentWorkflow) {
            multiAgentDeadline = Date.now() + MULTI_AGENT_WAIT_MS;
            await refreshMultiAgentWorkflow();
        }
    } else if (!succeeded) {
        scheduleMultiAgentPoll();
    }
}


async function refreshMultiAgentWorkflow() {
    if (!multiAgentEnabled || multiAgentBusy || !multiAgentWorkflow) {
        return;
    }

    stopMultiAgentPolling();
    multiAgentBusy = true;
    updateMultiAgentButtons();

    let succeeded = false;

    try {
        const workflow = await apiRequest(
            `${MULTI_AGENT_URL}/workflow/${multiAgentWorkflow.workflow_id}`
        );

        renderMultiAgentWorkflow(workflow);
        succeeded = true;
    } catch (error) {
        setMultiAgentStatus(
            `${error.message} Use Refresh workflow to try again.`
        );
    } finally {
        multiAgentBusy = false;
        updateMultiAgentButtons();
    }

    if (succeeded) {
        scheduleMultiAgentPoll();
    }
}


multiAgentForm.addEventListener("submit", async event => {
    event.preventDefault();

    if (multiAgentBusy || multiAgentStart.disabled) {
        return;
    }

    const userRequest = multiAgentRequest.value.trim();

    if (!userRequest) {
        setMultiAgentStatus("Enter a preparation request.");
        return;
    }

    stopMultiAgentPolling();
    multiAgentBusy = true;
    updateMultiAgentButtons();
    setMultiAgentStatus("Submitting preparation review...");

    let succeeded = false;

    try {
        const workflow = await apiRequest(
            `${MULTI_AGENT_URL}/workflow`,
            {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    user_request: userRequest
                })
            }
        );

        multiAgentCorrection.value = "";
        multiAgentDeadline = Date.now() + MULTI_AGENT_WAIT_MS;
        renderMultiAgentWorkflow(workflow);
        succeeded = true;
    } catch (error) {
        setMultiAgentStatus(error.message);
    } finally {
        multiAgentBusy = false;
        updateMultiAgentButtons();
    }

    if (succeeded) {
        scheduleMultiAgentPoll();
    }
});


multiAgentReviewForm.addEventListener("submit", async event => {
    event.preventDefault();

    if (
        !multiAgentEnabled ||
        multiAgentBusy ||
        multiAgentWorkflow?.status !== "pending_review"
    ) {
        return;
    }

    const decision = event.submitter?.value;
    const correction = multiAgentCorrection.value.trim();

    if (!["Accept", "Partially Accept", "Reject"].includes(decision)) {
        return;
    }

    if (decision === "Partially Accept" && !correction) {
        setMultiAgentStatus(
            "Enter a correction for partial acceptance."
        );
        return;
    }

    multiAgentBusy = true;
    updateMultiAgentButtons();

    try {
        const workflow = await apiRequest(
            `${MULTI_AGENT_URL}/workflow/${multiAgentWorkflow.workflow_id}/review`,
            {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    decision,
                    correction
                })
            }
        );

        renderMultiAgentWorkflow(workflow);
        setMultiAgentStatus(
            "Your decision was recorded. Checklist items were not changed."
        );
    } catch (error) {
        setMultiAgentStatus(
            `${error.message} Refresh the workflow before retrying.`
        );
    } finally {
        multiAgentBusy = false;
        updateMultiAgentButtons();
    }
});


multiAgentConnection.addEventListener(
    "click",
    checkMultiAgentConnection
);

multiAgentToggle.addEventListener("click", toggleMultiAgentMode);

multiAgentRefresh.addEventListener("click", () => {
    multiAgentDeadline = Date.now() + MULTI_AGENT_WAIT_MS;
    refreshMultiAgentWorkflow();
});

window.addEventListener("pagehide", stopMultiAgentPolling);

checkMultiAgentConnection();
