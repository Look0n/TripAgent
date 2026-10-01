const API_URL = "/api/accommodation/accommodations";
let isAdminView = false;
let currentView = "browse";


function showView(view) {

    currentView = view;

    const views = [
        "browse",
        "search",
        "ai",
        "admin"
    ];


    views.forEach(name => {

        document.getElementById(
            `${name}View`
        ).style.display =
            name === view
                ? "block"
                : "none";


        document.getElementById(
            `${name}Tab`
        ).classList.toggle(
            "active",
            name === view
        );
    });


    if (view === "browse") {

        loadAccommodations();

    }


    if (view === "admin") {

        loadAdminAccommodations();

    }
}


function showCustomerView() {

    isAdminView = false;

    document.getElementById(
        "adminView"
    ).style.display = "none";

    document.getElementById(
        "customerViewButton"
    ).classList.remove(
        "secondary-button"
    );

    document.getElementById(
        "adminViewButton"
    ).classList.add(
        "secondary-button"
    );

    loadAccommodations();
}


function showAdminView() {

    isAdminView = true;

    document.getElementById(
        "adminView"
    ).style.display = "block";

    document.getElementById(
        "customerViewButton"
    ).classList.add(
        "secondary-button"
    );

    document.getElementById(
        "adminViewButton"
    ).classList.remove(
        "secondary-button"
    );

    loadAccommodations();
}


async function loadAccommodations() {

    try {

        const response = await fetch(API_URL);

        const accommodations = await response.json();

        displayAccommodations(accommodations);

    } catch (error) {

        console.error("Error:", error);

        document.getElementById("accommodationList").innerHTML =
            "<p>Failed to load accommodations.</p>";
    }
}


function displayAccommodations(
    accommodations,
    targetId = "accommodationList",
    adminMode = false
) {
    const list = document.getElementById(targetId);

    list.innerHTML = "";

    if (!accommodations || accommodations.length === 0) {
        list.innerHTML = "<p>No accommodations found.</p>";
        return;
    }

    accommodations.forEach(accommodation => {

        const card = document.createElement("div");

        card.className = "accommodation-card";

        const imageUrl = accommodation.image_url
            ? `static/images/${
                accommodation.image_url.split("/").pop()
            }`
            : "";

        const adminButtons = adminMode
            ? `
                <button
                    class="secondary-button"
                    onclick="editAccommodation(
                        ${accommodation.accommodation_id}
                    )"
                >
                    Edit
                </button>

                <button
                    class="danger-button"
                    onclick="deleteAccommodation(
                        ${accommodation.accommodation_id}
                    )"
                >
                    Delete
                </button>
            `
            : "";

        card.innerHTML = `
            <img
                src="${imageUrl}"
                alt="${accommodation.accommodation_name}"
                class="accommodation-image"
            >

            <div class="accommodation-card-content">

                <div class="card-top">

                    <div>
                        <h3>
                            ${accommodation.accommodation_name}
                        </h3>

                        <p class="card-location">
                            ${accommodation.type}
                            ·
                            ${accommodation.city}
                        </p>
                    </div>

                    <span class="rating">
                        ★ ${accommodation.rating ?? "N/A"}
                    </span>

                </div>

                <p>
                    ${accommodation.address || ""}
                </p>

                <p class="price">
                    <strong>
                        $${accommodation.price_per_night}
                    </strong>
                    / night
                </p>

                <p>
                    Up to
                    ${accommodation.guest_capacity}
                    guest(s)
                </p>

                <div class="button-row">

                    <button
                        onclick="viewAccommodation(
                            ${accommodation.accommodation_id}
                        )"
                    >
                        View Details
                    </button>

                    ${adminButtons}

                </div>

            </div>
        `;

        list.appendChild(card);
    });
}

loadAccommodations();

async function searchAccommodations() {

    const city =
        document.getElementById("city").value.trim();

    const type =
        document.getElementById("type").value;

    const maxPrice =
        document.getElementById("maxPrice").value;


    const params = new URLSearchParams();


    if (city) {
        params.append("city", city);
    }

    if (type) {
        params.append("type", type);
    }

    if (maxPrice) {
        params.append("max_price", maxPrice);
    }


    try {

        const response = await fetch(
            `${API_URL}?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(
                "Search request failed"
            );
        }


        const accommodations =
            await response.json();


        displayAccommodations(
            accommodations,
            "searchResults",
            false
        );

    } catch (error) {

        console.error(
            "Search error:",
            error
        );

        document.getElementById(
            "searchResults"
        ).innerHTML =
            "<p>Unable to search accommodations.</p>";
    }
}


async function showAllSearchResults() {

    try {

        const response =
            await fetch(API_URL);

        const accommodations =
            await response.json();


        displayAccommodations(
            accommodations,
            "searchResults",
            false
        );

    } catch (error) {

        console.error(
            "Load error:",
            error
        );
    }
}


async function loadAdminAccommodations() {

    try {

        const response =
            await fetch(API_URL);

        const accommodations =
            await response.json();

        displayAccommodations(
            accommodations,
            "adminAccommodationList",
            true
        );

    } catch (error) {

        console.error(
            "Admin load error:",
            error
        );
    }
}


async function addAccommodation() {

    const accommodation = {
        accommodation_name:
            document.getElementById("addName").value,

        type:
            document.getElementById("addType").value,

        city:
            document.getElementById("addCity").value,

        address:
            document.getElementById("addAddress").value,

        price_per_night:
            Number(document.getElementById("addPrice").value),

        guest_capacity:
            Number(document.getElementById("addCapacity").value),

        rating:
            Number(document.getElementById("addRating").value),

        description:
        document.getElementById("addDescription").value,

        image_url:
            document.getElementById("addImage").value
    };


    try {

        const response = await fetch(API_URL, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(accommodation)
        });


        const result = await response.json();


        if (!response.ok) {

            document.getElementById("addMessage").textContent =
                result.error || "Failed to add accommodation.";

            return;
        }


        document.getElementById("addMessage").textContent =
            "Accommodation added successfully.";


        loadAccommodations();
        loadAdminAccommodations();


    } catch (error) {

        console.error("Add error:", error);

        document.getElementById("addMessage").textContent =
            "Failed to connect to the server.";
    }


}


function viewAccommodation(accommodationId) {

    const fromView =
        currentView === "admin"
            ? "admin"
            : "browse";

    window.location.href =
        `details/${accommodationId}?from=${fromView}`;
}


function editAccommodation(accommodationId) {
    window.location.href =
        `admin/edit/${accommodationId}`;
}


async function deleteAccommodation(id) {

    const confirmed = confirm(
        "Are you sure you want to delete this accommodation?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `${API_URL}/${id}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Delete failed.");
            return;
        }

        alert(result.message);

        loadAccommodations();
        loadAdminAccommodations();

    } catch (error) {
        console.error("Delete error:", error);
    }
}


async function getRecommendation() {

    const city =
        document.getElementById("aiCity").value;

    const budget =
        Number(document.getElementById("aiBudget").value);

    const guests =
        Number(document.getElementById("aiGuests").value);

    const type =
        document.getElementById("aiType").value;

    const preference =
        document.getElementById("aiPreference").value;

    const resultBox =
        document.getElementById("recommendationResult");


    if (!city || !budget || !guests) {

        resultBox.textContent =
            "Please enter city, budget and number of guests.";

        return;
    }


    let message =
    `Recommend accommodation in ${city}.`;


    if (budget) {
        message +=
            ` My budget is up to $${budget} per night.`;
    }


    if (guests) {
        message +=
            ` It is for ${guests} guest${guests > 1 ? "s" : ""}.`;
    }


    if (type) {
        message +=
            ` I prefer ${type}.`;
    }


    if (preference) {
        message +=
            ` I also prefer ${preference}.`;
    }


    resultBox.textContent =
        "Generating recommendation...";


    try {

        const response = await fetch(
            `${API_URL}/recommend`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );


        const result = await response.json();


        if (!response.ok) {

            resultBox.textContent =
                result.error || "Recommendation failed.";

            return;
        }


        resultBox.innerHTML = `
            <p>
                <strong>Matching accommodations:</strong>
                ${result.matches}
            </p>

            <p>
                ${result.reply}
            </p>
        `;


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        resultBox.textContent =
            "Unable to connect to the AI service.";
    }
}


async function sendChatMessage() {

    const input =
        document.getElementById("chatInput");

    const chatBox =
        document.getElementById("chatBox");

    const message = input.value.trim();


    if (!message) {
        return;
    }


    chatBox.innerHTML += `
        <p>
            <strong>You:</strong>
            ${message}
        </p>
    `;


    input.value = "";


    chatBox.innerHTML += `
        <p id="aiLoading">
            <strong>AI:</strong>
            Thinking...
        </p>
    `;


    try {

        const response = await fetch(
            `${API_URL}/recommend`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );


        const result = await response.json();


        document.getElementById("aiLoading").remove();


        if (!response.ok) {

            chatBox.innerHTML += `
                <p>
                    <strong>AI:</strong>
                    ${result.error}
                </p>
            `;

            return;
        }


        chatBox.innerHTML += `
            <p>
                <div class="chat-message">
                <strong>AI:</strong>
                    <div class="chat-reply">
                        ${result.reply}
                    </div>
                </div>
            </p>
        `;


    } catch (error) {

        const loading =
            document.getElementById("aiLoading");

        if (loading) {
            loading.remove();
        }


        chatBox.innerHTML += `
            <p>
                <strong>AI:</strong>
                Unable to connect to the AI service.
            </p>
        `;

        console.error(error);
    }
}


function handleChatKey(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendChatMessage();
    }
}


const params =
    new URLSearchParams(
        window.location.search
    );

const initialView =
    params.get("view");


if (initialView === "admin") {
    showView("admin");
} else if (initialView === "search") {
    showView("search");

} else if (initialView === "ai") {
    showView("ai");

} else {
    showView("browse");
}