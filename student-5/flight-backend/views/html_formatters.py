import html


LOW_SEAT_THRESHOLD = 10


def format_duration(minutes):
    hours = minutes // 60
    remainder = minutes % 60

    if hours and remainder:
        return f"{hours}h {remainder}m"

    if hours:
        return f"{hours}h"

    return f"{remainder}m"


def format_time(iso_timestamp):
    date_part, _, time_part = iso_timestamp.partition("T")

    return f"{date_part} {time_part[:5]}"


def format_flight_cards(flights):
    if not flights:
        return (
            '<p class="empty-state">'
            'No flights matched your search. Try a different route.'
            '</p>'
        )

    parts = ['<div class="flight-list">']

    for flight in flights:
        limited = flight["seat_availability"] < LOW_SEAT_THRESHOLD

        parts.append('<article class="flight-card">')

        parts.append(
            f'<h3>{html.escape(flight["airline"])} '
            f'<span class="flight-ref">#{flight["flight_id"]}</span></h3>'
        )

        parts.append(
            f'<p class="route">{html.escape(flight["origin"])} '
            f'&rarr; {html.escape(flight["destination"])}</p>'
        )

        parts.append(
            f'<p class="times">{format_time(flight["departure_time"])} '
            f'&ndash; {format_time(flight["arrival_time"])} '
            f'({format_duration(flight["duration"])})</p>'
        )

        parts.append(
            f'<p class="price">${flight["price"]:.2f}</p>'
        )

        if limited:
            parts.append(
                f'<p class="warning">Limited availability: '
                f'{flight["seat_availability"]} seats left</p>'
            )
        else:
            parts.append(
                f'<p class="seats">{flight["seat_availability"]} seats available</p>'
            )

        parts.append('</article>')

    parts.append('</div>')

    return "".join(parts)


def format_agentic_response(plan, act, observe, adapt):
    parts = ['<div class="agentic-loop">']

    parts.append('<section class="stage">')
    parts.append('<h4>Plan</h4>')
    parts.append(f'<p>Goal: {html.escape(plan["goal"])}</p>')
    parts.append(f'<p>Priority: {html.escape(plan["priority"])}</p>')
    parts.append('<ol>')

    for step in plan["steps"]:
        parts.append(f'<li>{html.escape(step)}</li>')

    parts.append('</ol>')
    parts.append('</section>')

    parts.append('<section class="stage">')
    parts.append('<h4>Act</h4>')
    parts.append(
        f'<p>Retrieved {act["flights_retrieved"]} flights from '
        f'{html.escape(act["source"])}</p>'
    )
    parts.append('</section>')

    parts.append('<section class="stage">')
    parts.append('<h4>Observe</h4>')
    parts.append(f'<p>{html.escape(observe["summary"])}</p>')

    if observe["warnings"]:
        parts.append('<ul class="warning-list">')

        for warning in observe["warnings"]:
            parts.append(f'<li>{html.escape(warning)}</li>')

        parts.append('</ul>')

    parts.append('</section>')

    parts.append('<section class="stage">')
    parts.append('<h4>Adapt</h4>')

    for paragraph in adapt.split("\n"):
        if paragraph.strip():
            parts.append(f'<p>{html.escape(paragraph.strip())}</p>')

    parts.append('</section>')

    parts.append('</div>')

    return "".join(parts)


def format_flight_table(flights):
    if not flights:
        return (
            '<p class="empty-state">'
            'No flights in the database.'
            '</p>'
        )

    parts = ['<table class="flight-table">']

    parts.append(
        '<thead><tr>'
        '<th>ID</th>'
        '<th>Airline</th>'
        '<th>Route</th>'
        '<th>Departure</th>'
        '<th>Duration</th>'
        '<th>Price</th>'
        '<th>Seats</th>'
        '<th></th>'
        '</tr></thead>'
    )

    parts.append('<tbody>')

    for flight in flights:
        parts.append('<tr>')

        parts.append(f'<td>{flight["flight_id"]}</td>')
        parts.append(f'<td>{html.escape(flight["airline"])}</td>')

        parts.append(
            f'<td>{html.escape(flight["origin"])} &rarr; '
            f'{html.escape(flight["destination"])}</td>'
        )

        parts.append(f'<td>{format_time(flight["departure_time"])}</td>')
        parts.append(f'<td>{format_duration(flight["duration"])}</td>')
        parts.append(f'<td>${flight["price"]:.2f}</td>')

        if flight["seat_availability"] < LOW_SEAT_THRESHOLD:
            parts.append(
                f'<td class="warning">{flight["seat_availability"]}</td>'
            )
        else:
            parts.append(f'<td>{flight["seat_availability"]}</td>')

        parts.append(
            f'<td><button class="link-button" '
            f'hx-delete="/api/flight/flights/{flight["flight_id"]}/html" '
            f'hx-target="#flight-table" '
            f'hx-swap="innerHTML" '
            f'hx-confirm="Delete flight {flight["flight_id"]}?">'
            f'Delete</button></td>'
        )

        parts.append('</tr>')

    parts.append('</tbody>')
    parts.append('</table>')

    return "".join(parts)