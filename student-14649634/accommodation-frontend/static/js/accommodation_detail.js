const accommodationId =
    document.body.dataset.accommodationId;


    const params =
    new URLSearchParams(
        window.location.search
    );
    
    const fromView =
    params.get("from");
    
    
    const backLink =
    document.getElementById(
        "backLink"
    );
    
    if (backLink) {

        if (fromView === "admin") {
        
        backLink.href =
            "/accommodation/?view=admin";
        
        backLink.textContent =
            "← Back to Admin View";
        
        } else {
        
        backLink.href =
            "/accommodation/?view=browse";
        
        backLink.textContent =
            "← Back to Browse";
        }
    }

async function loadAccommodation() {

    const response = await fetch(
        `/api/accommodation/accommodations/${accommodationId}`
    );

    const accommodation =
        await response.json();


    const imageFile =
    accommodation.image_url
        ? accommodation.image_url.split("/").pop()
        : "";


    document
        .getElementById("detailContent")
        .innerHTML = `

            <h1>
                ${accommodation.accommodation_name}
            </h1>

            <p class="subtitle">
                ${accommodation.type}
                ·
                ${accommodation.city}
            </p>

            <img
                class="detail-image"
                src="/accommodation/static/images/${imageFile}"
                alt="${accommodation.accommodation_name}"
            >

            <div class="detail-grid">

                <div>
                    <strong>Address</strong>

                    <p>
                        ${accommodation.address || "-"}
                    </p>
                </div>

                <div>
                    <strong>Price Per Night</strong>

                    <p>
                        $${accommodation.price_per_night}
                    </p>
                </div>

                <div>
                    <strong>Guest Capacity</strong>

                    <p>
                        ${accommodation.guest_capacity}
                    </p>
                </div>

                <div>
                    <strong>Rating</strong>

                    <p>
                        ★ ${accommodation.rating ?? "N/A"}
                    </p>
                </div>

            </div>

            <h2>Description</h2>

            <p class="description">
                ${accommodation.description || ""}
            </p>

            <div class="availability-card">

            <h2>
                Check Availability
            </h2>

            <p class="availability-help">
                Select your check-in and
                check-out dates.
            </p>


            <div class="availability-form">

                <div class="availability-field">

                    <label for="checkIn">
                        Check-in
                    </label>

                    <input
                        type="date"
                        id="checkIn"
                    >

                </div>


                <div class="availability-field">

                    <label for="checkOut">
                        Check-out
                    </label>

                    <input
                        type="date"
                        id="checkOut"
                    >

                </div>


                <button
                    type="button"
                    class="primary-button"
                    onclick="checkAvailability()"
                >
                    Check Availability
                </button>

            </div>


            <div
                id="availabilityResult"
                class="availability-result"
            ></div>

        </div>
        `;

    document
    .getElementById("checkIn")
    .addEventListener(
        "change",
        function () {

            const checkOut =
                document.getElementById(
                    "checkOut"
                );

            checkOut.min =
                this.value;


            if (
                checkOut.value
                &&
                checkOut.value <= this.value
            ) {
                checkOut.value = "";
            }
        }
    );
        
}


async function checkAvailability() {

    const checkIn =
        document.getElementById(
            "checkIn"
        ).value;

    const checkOut =
        document.getElementById(
            "checkOut"
        ).value;

    const resultContainer =
        document.getElementById(
            "availabilityResult"
        );


    if (!checkIn || !checkOut) {

        resultContainer.innerHTML = `
            <div class="availability-error">
                Please select both
                check-in and check-out dates.
            </div>
        `;

        return;
    }


    if (checkOut <= checkIn) {

        resultContainer.innerHTML = `
            <div class="availability-error">
                Check-out must be after
                check-in.
            </div>
        `;

        return;
    }


    resultContainer.innerHTML = `
        <div class="availability-loading">
            Checking availability...
        </div>
    `;


    try {

        const response = await fetch(
            `/api/accommodation/accommodations/${accommodationId}/availability`
            + `?check_in=${encodeURIComponent(checkIn)}`
            + `&check_out=${encodeURIComponent(checkOut)}`
        );


        const result =
            await response.json();


        if (!response.ok) {

            resultContainer.innerHTML = `
                <div class="availability-error">
                    ${result.error
                        || "Unable to check availability."}
                </div>
            `;

            return;
        }


        // check availability first
        if (result.status === "unknown") {

            resultContainer.innerHTML = `
                <div class="availability-info">

                    <strong>
                        Availability Information Unavailable
                    </strong>

                    <p>
                        ${result.message ||
                        "Availability information is not available. Please contact the hotel."}
                    </p>

                </div>
            `;

            return;
        }

        if (result.available) {

            resultContainer.innerHTML = `
                <div class="availability-success">

                    <strong>
                        ✓ Available
                    </strong>

                    <p>
                        This accommodation
                        is available from
                        ${formatDate(checkIn)}
                        to
                        ${formatDate(checkOut)}.
                    </p>

                    <p>
                        ${result.number_of_nights}
                        night${result.number_of_nights !== 1
                            ? "s"
                            : ""}
                    </p>

                </div>
            `;

        } else {

            let unavailableText = "";

            if (
                result.unavailable_dates
                &&
                result.unavailable_dates.length > 0
            ) {

                unavailableText = `
                    <p>
                        Unavailable date(s):
                        ${result.unavailable_dates
                            .map(formatDate)
                            .join(", ")}
                    </p>
                `;
            }


            resultContainer.innerHTML = `
                <div class="availability-error">

                    <strong>
                        ✕ Not Available
                    </strong>

                    <p>
                        This accommodation
                        is not available for
                        the selected dates.
                    </p>

                    ${unavailableText}

                </div>
            `;
        }


    } catch (error) {

        console.error(
            "Availability error:",
            error
        );

        resultContainer.innerHTML = `
            <div class="availability-error">
                Unable to check availability.
            </div>
        `;
    }
}


function formatDate(dateString) {

    const date =
        new Date(
            `${dateString}T00:00:00`
        );


    return date.toLocaleDateString(
        "en-AU",
        {
            day: "numeric",
            month: "short",
            year: "numeric"
        }
    );
}


function setMinimumDates() {

    const today =
        new Date();

    const todayString =
        today
            .toISOString()
            .split("T")[0];


    document
        .getElementById("checkIn")
        .min =
        todayString;


    document
        .getElementById("checkOut")
        .min =
        todayString;
}

loadAccommodation();
setMinimumDates();
