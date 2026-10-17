// ============================================================
// Accommodation Multi-Agent UI
// Planner -> Worker -> Reviewer -> Human Review
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        clearWorkflowResults();

        setWorkflowMessage(
            "No workflow started."
        );

        setServerStatus(
            "off",
            "Checking Multi-Agent server..."
        );

        setReviewButtonsEnabled(false);

        await loadMultiAgentMode();
    }
);


let currentWorkflowId = null;
let workflowPollingTimer = null;


// ------------------------------------------------------------
// DOM Elements
// ------------------------------------------------------------

const multiAgentEnabled =
    document.getElementById("multiAgentEnabled");

const multiAgentModeStatus =
    document.getElementById("multiAgentModeStatus");

const multiAgentServerStatusText =
    document.getElementById("multiAgentServerStatusText");

const multiAgentServerStatusDot =
    document.getElementById("multiAgentServerStatusDot");

const accommodationRequest =
    document.getElementById("accommodationRequest");

const runWorkflowButton =
    document.getElementById("runWorkflowButton");

const workflowStatusText =
    document.getElementById("workflowStatusText");

const plannerResult =
    document.getElementById("plannerResult");

const workerResult =
    document.getElementById("workerResult");

const reviewerResult =
    document.getElementById("reviewerResult");

const workflowSummary =
    document.getElementById("workflowSummary");

const correctionInput =
    document.getElementById("correctionInput");

const humanReviewResult =
    document.getElementById("humanReviewResult");

const acceptButton =
    document.getElementById("acceptButton");

const partialAcceptButton =
    document.getElementById("partialAcceptButton");

const rejectButton =
    document.getElementById("rejectButton");


// ------------------------------------------------------------
// Helpers
// ------------------------------------------------------------

function setServerStatus(type, text) {

    multiAgentServerStatusText.textContent = text;

    multiAgentServerStatusDot.className =
        "status-dot";

    if (type === "on") {
        multiAgentServerStatusDot.classList.add(
            "status-on"
        );

        workflowStatusText.textContent("No workflow started.");
    }
    else if (type === "off") {
        multiAgentServerStatusDot.classList.add(
            "status-off"
        );
    }
    else {
        multiAgentServerStatusDot.classList.add(
            "status-error"
        );
    }
}


function setModeDisplay(enabled) {

    multiAgentEnabled.checked = enabled;

    multiAgentModeStatus.textContent =
        enabled ? "ON" : "OFF";
}


function setWorkflowMessage(message) {

    workflowStatusText.textContent = message;
}


function setReviewButtonsEnabled(enabled) {

    acceptButton.disabled = !enabled;
    partialAcceptButton.disabled = !enabled;
    rejectButton.disabled = !enabled;
}


function clearWorkflowResults() {

    plannerResult.textContent =
        "Waiting for a workflow.";

    workerResult.textContent =
        "Waiting for a workflow.";

    reviewerResult.textContent =
        "Waiting for a workflow.";

    workflowSummary.textContent =
        "Generate an accommodation recommendation to see the review summary.";

    humanReviewResult.textContent =
        "No decision recorded.";

    correctionInput.value = "";

    setReviewButtonsEnabled(false);
}


// ------------------------------------------------------------
// Load Multi-Agent mode
// ------------------------------------------------------------

async function loadMultiAgentMode() {

    try {

        const response = await fetch(
            `${window.API_URL}/multi-agent/mode`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to load Multi-Agent mode."
            );
        }

        setModeDisplay(
            Boolean(data.enabled)
        );

        if (data.locked) {

            multiAgentEnabled.disabled = true;

            multiAgentModeStatus.textContent =
                "LOCKED";

            setServerStatus(
                "off",
                "Multi-Agent is disabled by deployment configuration."
            );

            return;
        }

        multiAgentEnabled.disabled = false;

        if (data.enabled) {
            await checkMultiAgentHealth();
        }
        else {
            setServerStatus(
                "off",
                "Multi-Agent mode is OFF."
            );
        }

    }
    catch (error) {

        console.error(
            "Mode load error:",
            error
        );

        setServerStatus(
            "error",
            "Unable to check Multi-Agent mode."
        );
    }
}


// ------------------------------------------------------------
// Toggle Multi-Agent mode
// ------------------------------------------------------------

async function updateMultiAgentMode() {

    const requestedState =
        multiAgentEnabled.checked;

    multiAgentEnabled.disabled = true;

    try {

        const response = await fetch(
            `${window.API_URL}/multi-agent/mode`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    enabled: requestedState
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to update Multi-Agent mode."
            );
        }

        setModeDisplay(
            Boolean(data.enabled)
        );

        if (data.enabled) {

            await checkMultiAgentHealth();

        }
        else {

            stopWorkflowPolling();

            setServerStatus(
                "off",
                "Multi-Agent mode is OFF."
            );

            setWorkflowMessage(
                "Multi-Agent mode is OFF."
            );

            setReviewButtonsEnabled(false);
        }

    }
    catch (error) {

        console.error(
            "Mode update error:",
            error
        );

        // Return checkbox to previous state
        multiAgentEnabled.checked =
            !requestedState;

        setModeDisplay(
            !requestedState
        );

        setServerStatus(
            "error",
            error.message
        );
    }
    finally {

        multiAgentEnabled.disabled = false;
    }
}


// ------------------------------------------------------------
// Health check
// ------------------------------------------------------------

async function checkMultiAgentHealth() {

    try {

        const response = await fetch(
            `${window.API_URL}/multi-agent/health`
        );

        const data = await response.json();

        if (!response.ok) {

            if (response.status === 403) {

                setServerStatus(
                    "off",
                    data.error ||
                    "Multi-Agent mode is OFF."
                );

                return false;
            }

            throw new Error(
                data.error ||
                "Multi-Agent server unavailable."
            );
        }

        setServerStatus(
            "on",
            "Connected to shared Multi-Agent server."
        );

        return true;

    }
    catch (error) {

        console.error(
            "Health check error:",
            error
        );

        setServerStatus(
            "error",
            "Unable to connect to shared Multi-Agent server."
        );

        return false;
    }
}


// ------------------------------------------------------------
// Start workflow
// ------------------------------------------------------------

async function runWorkflow() {

    const userRequest =
        accommodationRequest.value.trim();

    if (!userRequest) {

        alert(
            "Please enter an accommodation request."
        );

        return;
    }

    if (!multiAgentEnabled.checked) {

        alert(
            "Please enable Multi-Agent mode first."
        );

        return;
    }

    stopWorkflowPolling();

    currentWorkflowId = null;

    clearWorkflowResults();

    runWorkflowButton.disabled = true;

    runWorkflowButton.textContent =
        "Starting Workflow...";

    setWorkflowMessage(
        "Creating workflow..."
    );

    try {

        const response = await fetch(
            `${window.API_URL}/multi-agent/workflow`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    user_request: userRequest
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to start workflow."
            );
        }

        currentWorkflowId =
            data.workflow_id;

        setWorkflowMessage(
            `Workflow started: ${data.status}`
        );

        if (!currentWorkflowId) {

            throw new Error(
                "Workflow ID was not returned."
            );
        }

        // First status request immediately
        await loadWorkflowStatus();

        // Continue polling
        startWorkflowPolling();

    }
    catch (error) {

        console.error(
            "Workflow start error:",
            error
        );

        setWorkflowMessage(
            `Error: ${error.message}`
        );

        runWorkflowButton.disabled = false;

        runWorkflowButton.textContent =
            "Run Workflow";
    }
}


// ------------------------------------------------------------
// Poll workflow
// ------------------------------------------------------------

function startWorkflowPolling() {

    stopWorkflowPolling();

    workflowPollingTimer =
        setInterval(
            loadWorkflowStatus,
            2500
        );
}


function stopWorkflowPolling() {

    if (workflowPollingTimer) {

        clearInterval(
            workflowPollingTimer
        );

        workflowPollingTimer = null;
    }
}


// ------------------------------------------------------------
// Get workflow status
// ------------------------------------------------------------

async function loadWorkflowStatus() {

    if (!currentWorkflowId) {
        return;
    }

    try {

        const response = await fetch(
            `${window.API_URL}/multi-agent/workflow/${currentWorkflowId}`
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to retrieve workflow."
            );
        }

        renderWorkflow(data);

        const status =
            data.status || "unknown";

        if (
            status === "pending_review" ||
            status === "completed" ||
            status === "rejected" ||
            status === "failed"
        ) {

            stopWorkflowPolling();

            runWorkflowButton.disabled =
                false;

            runWorkflowButton.textContent =
                "Run Workflow";
        }

    }
    catch (error) {

        console.error(
            "Workflow polling error:",
            error
        );

        stopWorkflowPolling();

        setWorkflowMessage(
            `Error: ${error.message}`
        );

        runWorkflowButton.disabled =
            false;

        runWorkflowButton.textContent =
            "Run Workflow";
    }
}


// ------------------------------------------------------------
// Render Planner / Worker / Reviewer
// ------------------------------------------------------------

function renderWorkflow(workflow) {

    const status =
        workflow.status || "unknown";

    setWorkflowMessage(
        `Workflow status: ${status}`
    );


    // -------------------------
    // Planner
    // -------------------------

    if (
        workflow.planner_result &&
        workflow.planner_result.plan
    ) {

        plannerResult.textContent =
            workflow.planner_result.plan;
    }
    else if (
        status === "queued"
    ) {

        plannerResult.textContent =
            "Waiting for Planner...";
    }


    // -------------------------
    // Worker
    // -------------------------

    if (
        workflow.worker_result &&
        workflow.worker_result.output
    ) {

        workerResult.textContent =
            workflow.worker_result.output;
    }
    else if (
        workflow.planner_result
    ) {

        workerResult.textContent =
            "Waiting for Worker...";
    }


    // -------------------------
    // Reviewer
    // -------------------------

    if (
        workflow.reviewer_result &&
        workflow.reviewer_result.review
    ) {

        reviewerResult.textContent =
            workflow.reviewer_result.review;
    }
    else if (
        workflow.worker_result
    ) {

        reviewerResult.textContent =
            "Waiting for Reviewer...";
    }


    // -------------------------
    // Human review summary
    // -------------------------

    if (status === "pending_review") {

        workflowSummary.textContent =
            buildWorkflowSummary(workflow);

        setReviewButtonsEnabled(true);
    }
    else {

        setReviewButtonsEnabled(false);
    }


    // -------------------------
    // Completed human decision
    // -------------------------

    if (
        workflow.human_decision &&
        workflow.human_decision.status ===
            "completed"
    ) {

        const human =
            workflow.human_decision;

        humanReviewResult.textContent =
            `Decision: ${human.decision}` +
            (
                human.correction
                    ? `\nCorrection: ${human.correction}`
                    : ""
            );

        setReviewButtonsEnabled(false);
    }


    // -------------------------
    // Failed workflow
    // -------------------------

    if (status === "failed") {

        workflowSummary.textContent =
            workflow.error ||
            "Workflow failed.";

        setReviewButtonsEnabled(false);
    }
}


// ------------------------------------------------------------
// Human review summary
// ------------------------------------------------------------

function buildWorkflowSummary(workflow) {

    const worker =
        workflow.worker_result?.output ||
        "No Worker result.";

    const reviewer =
        workflow.reviewer_result?.review ||
        "No Reviewer result.";

    return (
        "Worker recommendation:\n" +
        worker +
        "\n\nReviewer assessment:\n" +
        reviewer
    );
}


// ------------------------------------------------------------
// Submit Human Review
// ------------------------------------------------------------

async function submitHumanReview(decision) {

    if (!currentWorkflowId) {

        alert(
            "No workflow is available for review."
        );

        return;
    }

    const correction =
        correctionInput.value.trim();

    if (
        decision === "Partially Accept" &&
        !correction
    ) {

        alert(
            "Please enter a correction for Partial Acceptance."
        );

        correctionInput.focus();

        return;
    }

    setReviewButtonsEnabled(false);

    humanReviewResult.textContent =
        "Recording human review...";

    try {

        const response = await fetch(
            `${window.API_URL}/multi-agent/review`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    workflow_id:
                        currentWorkflowId,

                    decision:
                        decision,

                    correction:
                        correction
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to record human review."
            );
        }

        renderWorkflow(data);

        humanReviewResult.textContent =
            `Decision recorded: ${decision}` +
            (
                correction
                    ? `\nCorrection: ${correction}`
                    : ""
            );

        setWorkflowMessage(
            `Workflow status: ${data.status}`
        );

    }
    catch (error) {

        console.error(
            "Human review error:",
            error
        );

        humanReviewResult.textContent =
            `Error: ${error.message}`;

        // Allow another attempt if it failed
        setReviewButtonsEnabled(true);
    }
}


// ------------------------------------------------------------
// Sample request
// ------------------------------------------------------------

function useAccommodationSample() {

    accommodationRequest.value =
        "Find suitable accommodation in Sydney under $300.";
}


// ------------------------------------------------------------
// Event listeners
// ------------------------------------------------------------

multiAgentEnabled.addEventListener(
    "change",
    updateMultiAgentMode
);


runWorkflowButton.addEventListener(
    "click",
    runWorkflow
);


acceptButton.addEventListener(
    "click",
    () => {
        submitHumanReview(
            "Accept"
        );
    }
);


partialAcceptButton.addEventListener(
    "click",
    () => {
        submitHumanReview(
            "Partially Accept"
        );
    }
);


rejectButton.addEventListener(
    "click",
    () => {
        submitHumanReview(
            "Reject"
        );
    }
);


// ------------------------------------------------------------
// Page startup
// ------------------------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        clearWorkflowResults();

        setWorkflowMessage(
            "No workflow started."
        );

        setServerStatus(
            "off",
            "Checking Multi-Agent server..."
        );

        setReviewButtonsEnabled(false);

        await loadMultiAgentMode();
    }
);