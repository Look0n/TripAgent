# TripAgent Shared MCP Tool Contracts

## Scope

The current shared MCP integration exposes **10 tools**:

- 5 Account feature tools.
- 5 shared TripAgent tools.

The Account feature is intended to use only these Account and shared tools.
Other feature-specific tools can be registered later by their owning features.

The MCP server runs locally on port `7001` and uses Streamable HTTP at `/mcp`.

## Identity and access rule

Customer identity must come from the authenticated TripAgent Account backend
integration. The browser must not be trusted to select another customer's ID.
When the Account backend calls a customer-specific MCP tool, it must inject the
`customer_id` derived from the gateway's `X-Customer-ID` header.

---

## Account tools

### `get_customer_profile`

Retrieves the existing Account profile.

**Input**

- `customer_id: int`

**Uses**

- `GET /api/account/profile`

**Output**

- `success`
- `customer_id`
- `profile`

### `get_customer_preferences`

Retrieves the six preference fields used by the current Account feature.

**Input**

- `customer_id: int`

**Uses**

- `GET /api/account/preferences`

**Preference fields**

- `budget_level`
- `travel_style`
- `accommodation_type`
- `transport_preference`
- `food_preference`
- `pace_preference`

### `update_customer_preferences`

Updates supported Account preference fields. Unsupported keys are discarded.

**Input**

- `customer_id: int`
- `preferences: object`

**Uses**

- `PUT /api/account/preferences`

### `get_customer_summary`

Retrieves both the current profile and current preferences for use as compact
AI context.

**Input**

- `customer_id: int`

### `check_profile_completeness`

Checks the required Account profile fields and all six travel preference fields.

Required profile fields are `first_name`, `last_name`, and `email`. `phone` and
`country` remain optional because the current Account schema allows them to be
empty.

---

## Shared TripAgent tools

### `list_tripagent_services`

Lists the five feature services currently defined in `docker-compose.yml`:

- Account
- Accommodation
- Attractions
- Checklist
- Flight

### `get_service_status`

Checks a feature backend's `/health` endpoint through its host-published port.

**Input**

- `service_name: str`

### `list_available_tools`

Returns the MCP tools explicitly registered for a feature.

**Input**

- `feature: str` (defaults to `account`)

The current Account registration returns the five Account tools plus the five
shared TripAgent tools.

### `get_tripagent_help`

Returns static help for a supported topic.

**Input**

- `topic: str` (`general`, `account`, `mcp`, or `rag`)

### `get_system_summary`

Returns non-sensitive information about the current TripAgent architecture,
including the shared gateway and local MCP/RAG ports.

---

## Current service addresses from the project

Because the MCP server runs on the host machine, it uses the ports published by
Docker:

| Service | Host address |
|---|---|
| Account backend | `http://localhost:5001` |
| Accommodation backend | `http://localhost:5002` |
| Attractions backend | `http://localhost:5003` |
| Checklist backend | `http://localhost:5004` |
| Flight backend | `http://localhost:5005` |
| Shared gateway | `http://localhost:5050` |
| Shared MCP | `http://localhost:7001/mcp` |
| Shared RAG HTTP | `http://localhost:7002` |
