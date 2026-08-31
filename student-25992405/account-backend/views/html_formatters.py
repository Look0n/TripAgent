from markupsafe import escape


def format_customer_html(customer):
    if not customer:
        return "<p>Customer not found.</p>"

    return f"""
    <div class="customer-profile">
        <h2>{escape(customer.get("first_name", ""))} {escape(customer.get("last_name", ""))}</h2>
        <p><strong>Email:</strong> {escape(customer.get("email", ""))}</p>
        <p><strong>Phone:</strong> {escape(customer.get("phone", ""))}</p>
        <p><strong>Country:</strong> {escape(customer.get("country", ""))}</p>
    </div>
    """


def format_preferences_html(preferences):
    if not preferences:
        return "<p>No travel preferences saved yet.</p>"

    return f"""
    <div class="travel-preferences">
        <p><strong>Budget:</strong> {escape(preferences.get("budget_level", ""))}</p>
        <p><strong>Travel style:</strong> {escape(preferences.get("travel_style", ""))}</p>
        <p><strong>Accommodation:</strong> {escape(preferences.get("accommodation_type", ""))}</p>
        <p><strong>Transport:</strong> {escape(preferences.get("transport_preference", ""))}</p>
        <p><strong>Food:</strong> {escape(preferences.get("food_preference", ""))}</p>
        <p><strong>Pace:</strong> {escape(preferences.get("pace_preference", ""))}</p>
    </div>
    """
