import json
from time import perf_counter
from urllib import error, parse, request

from config.review_config import ENDPOINT_TIMEOUT_SECONDS


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_json(base_url, path):
    started = perf_counter()
    result = {"method": "GET", "path": path, "actual_status": None}
    try:
        req = request.Request(base_url.rstrip("/") + path, headers={"Accept": "application/json"}, method="GET")
        opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
        try:
            response = opener.open(req, timeout=ENDPOINT_TIMEOUT_SECONDS)
        except error.HTTPError as http_error:
            response = http_error
        with response:
            result["actual_status"] = response.code
            result["json_content_type"] = response.headers.get_content_type() == "application/json"
            raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            result["error"] = "Response exceeds 1 MiB validation limit"
            payload = None
        else:
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeError):
                result["error"] = "Response is not valid JSON"
                payload = None
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        result["error"] = f"HTTP collection failed: {type(exc).__name__}"
        payload = None
    result["elapsed_ms"] = round((perf_counter() - started) * 1000)
    return result, payload


def collect_endpoints_context(service_config):
    config = service_config.get("endpoints", {})
    evidence = {
        "service": service_config.get("name", "Unknown"),
        "scope": "Direct backend; unauthenticated; GET-only HTTP checks",
        "not_run": ["CRUD writes", "authenticated account access", "gateway/frontend integration", "user AI-mode"],
        "checks": [],
    }
    base_url = config.get("base_url", "")
    parsed = parse.urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1") or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        evidence["error"] = "Expected a configured local HTTP backend URL"
        evidence["validation_status"] = "UNAVAILABLE"
        return False, evidence
    evidence["base_url"] = base_url
    checks = evidence["checks"]

    def check(path, status=200, shape="object", equals=None, error_required=False, row_equals=None, id_field=None):
        result, payload = get_json(base_url, path)
        result.update({"expected_status": status, "expected_shape": shape})
        failures = []
        if result["actual_status"] != status:
            failures.append("Unexpected HTTP status")
        if result.get("error"):
            failures.append(result["error"])
        if not result.get("json_content_type", False):
            failures.append("Expected application/json")
        valid_shape = isinstance(payload, list) if shape == "array" else isinstance(payload, dict)
        if not valid_shape:
            failures.append(f"Expected JSON {shape}")
        else:
            if isinstance(payload, dict):
                if equals and any(key not in payload or type(payload[key]) is not type(value) or payload[key] != value for key, value in equals.items()):
                    failures.append("Expected response field values do not match")
                if error_required and (not isinstance(payload.get("error"), str) or not payload["error"].strip()):
                    failures.append("Expected non-empty error field")
            else:
                result["row_count"] = len(payload)
                if any(not isinstance(row, dict) for row in payload):
                    failures.append("Expected object rows")
                elif id_field and any(type(row.get(id_field)) is not int for row in payload):
                    failures.append("Expected integer row IDs")
                elif row_equals and any(any(row.get(key) != value for key, value in row_equals.items()) for row in payload):
                    failures.append("Filter returned mismatching rows")
        result["status"] = "FAIL" if failures else "PASS"
        result["findings"] = failures
        if equals:
            result["expected_fields"] = equals
        if row_equals:
            result["expected_row_fields"] = row_equals
            if isinstance(payload, list) and not payload:
                result["limitation"] = "No matching rows; filter correctness not demonstrated"
                if not failures:
                    result["status"] = "SKIPPED"
        checks.append(result)
        return payload if not failures else None

    check("/health", equals={"status": config.get("health_status"), "service": config.get("health_service")})
    for item in config.get("checks", []):
        check(item["path"], status=item["status"], equals=item.get("equals"), error_required=item.get("error_required", False))
    list_path = config.get("list_path")
    if list_path:
        id_field = config["id_field"]
        rows = check(list_path, shape="array", id_field=id_field)
        if rows:
            selected_id = rows[0][id_field]
            check(f"{list_path}/{selected_id}", equals={id_field: selected_id})
        else:
            checks.append({"method": "GET", "path": f"{list_path}/{{id}}", "status": "SKIPPED", "reason": "No validated row available for detail lookup"})
        for filter_config in config.get("filters", []):
            field = filter_config["field"]
            value = filter_config.get("value")
            if value is None and rows:
                value = rows[0].get(field)
            if value is None:
                checks.append({"method": "GET", "path": list_path, "status": "SKIPPED", "reason": f"No observed value for {field} filter"})
                continue
            path = list_path + "?" + parse.urlencode({field: value})
            check(path, shape="array", row_equals={field: value}, id_field=id_field)
    available = any(item.get("actual_status") is not None for item in checks)
    evidence["validation_status"] = (
        "UNAVAILABLE" if not available else
        "FAIL" if any(item["status"] == "FAIL" for item in checks) else
        "PARTIAL" if any(item["status"] == "SKIPPED" for item in checks) else "PASS"
    )
    return available, evidence
