import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import urlsplit

from config.review_config import COMPOSE_TIMEOUT_SECONDS


REPO_ROOT = Path(__file__).resolve().parents[2]


def compose_json(root, arguments):
    command = ["docker", "compose", "--project-directory", str(root), "-f", str(root / "docker-compose.yml"), *arguments]
    try:
        response = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=COMPOSE_TIMEOUT_SECONDS)
        if response.returncode:
            return None, f"Compose {' '.join(arguments)} failed (exit {response.returncode}); inspect locally for details"
        text = response.stdout.strip()
        if not text:
            return [], None
        try:
            return json.loads(text), None
        except ValueError:
            return [json.loads(line) for line in text.splitlines() if line.strip()], None
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return None, f"Compose collection failed: {type(exc).__name__}"


def collect_project_context(repo_root=REPO_ROOT):
    root = Path(repo_root).resolve()
    snapshot = {"root": root, "config": None, "containers": None}
    if not (root / "docker-compose.yml").is_file():
        snapshot["config_error"] = "Missing docker-compose.yml"
        return snapshot
    config, config_error = compose_json(root, ["config", "--format", "json"])
    if not isinstance(config, dict) or not isinstance(config.get("services"), dict):
        snapshot["config_error"] = config_error or "Invalid Compose configuration response"
    else:
        snapshot["config"] = config
    containers, runtime_error = compose_json(root, ["ps", "--all", "--format", "json"])
    if isinstance(containers, dict):
        containers = [containers]
    if isinstance(containers, list) and all(isinstance(item, dict) for item in containers):
        snapshot["containers"] = containers
    else:
        snapshot["runtime_error"] = runtime_error or "Invalid Compose runtime response"
    return snapshot


def collect_architecture_context(service_config, project_context=None):
    snapshot = project_context if project_context is not None else collect_project_context()
    root = snapshot["root"]
    settings = service_config.get("architecture", {})
    evidence = {
        "service": service_config["name"],
        "frontend_type": settings.get("frontend_type", "unknown"),
        "scope": "Selected service set plus shared homepage/proxy/gateway configuration and Compose runtime status",
        "checks": [], "runtime": [],
        "not_verified": ["browser interactions", "authenticated gateway requests", "inter-service HTTP connectivity",
                         "CRUD", "restart persistence", "image freshness versus local files", "full Nginx syntax", "CI/CD", "user AI-mode"],
    }
    checks = evidence["checks"]

    def add(name, passed, observed):
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": observed})

    def file_exists(relative):
        path = (root / relative).resolve()
        valid = path.is_relative_to(root) and path.is_file()
        add(f"File: {relative}", valid, "present" if valid else "missing or outside repository")

    for key in ("frontend_dir", "backend_dir", "database_dir"):
        path = (root / service_config[key]).resolve()
        add(f"Directory: {service_config[key]}", path.is_relative_to(root) and path.is_dir(), service_config[key])
    required = [service_config["backend_path"], service_config["database_dir"] + "/app.py"]
    required += [service_config["frontend_dir"] + "/" + name for name in settings.get("frontend_files", [])]
    required += ["shared/frontend/index.html", "shared/frontend/nginx.conf", "shared/frontend/css/styles.css"]
    for relative in required:
        file_exists(relative)
    config = snapshot.get("config")
    if not settings or config is None:
        evidence["configuration_status"] = "UNAVAILABLE"
        evidence["runtime_status"] = "UNAVAILABLE"
        evidence["validation_status"] = "UNAVAILABLE"
        evidence["error"] = snapshot.get("config_error", "Missing architecture service configuration")
        return False, evidence
    services = config["services"]
    for shared in ("shared-frontend", "shared-gateway"):
        add(f"Shared Compose service: {shared}", shared in services, "defined" if shared in services else "missing")
    frontend = settings["frontend_service"]
    backend = settings["backend_service"]
    database = service_config["database_service"]
    backend_port = urlsplit(service_config["endpoints"]["base_url"]).port
    roles = [
        (frontend, service_config["frontend_dir"], settings["frontend_port"]),
        (backend, service_config["backend_dir"], backend_port),
        (database, service_config["database_dir"], settings["database_port"]),
    ]
    for name, directory, port in roles:
        entry = services.get(name)
        add(f"Compose service: {name}", isinstance(entry, dict), "defined" if isinstance(entry, dict) else "missing")
        if not isinstance(entry, dict):
            continue
        build = entry.get("build", {})
        if isinstance(build, str):
            build = {"context": build}
        context = (root / build.get("context", "__missing__")).resolve()
        expected = (root / directory).resolve()
        add(f"Build context: {name}", context == expected and context.is_dir(), directory if context == expected else "does not match assigned directory")
        dockerfile = (context / build.get("dockerfile", "Dockerfile")).resolve()
        valid = dockerfile.is_relative_to(expected) and dockerfile.is_file()
        if not valid and build.get("dockerfile", "Dockerfile") == "Dockerfile":
            dockerfile = context / "dockerfile"
            valid = dockerfile.is_relative_to(expected) and dockerfile.is_file()
        add(f"Dockerfile: {name}", valid, "present" if valid else "missing or outside assigned directory")
        ports = [{"published": str(p.get("published", "")), "target": p.get("target"), "protocol": p.get("protocol", "tcp")}
                 for p in entry.get("ports", []) if isinstance(p, dict)]
        add(f"Container port mapping: {name}", any(str(p["target"]) == str(port) and p["protocol"] == "tcp" for p in ports), ports)
        if name == backend:
            expected_published = str(urlsplit(service_config["endpoints"]["base_url"]).port)
            add("Backend host port matches endpoint configuration",
                any(p["published"] == expected_published and str(p["target"]) == str(port) for p in ports), ports)
        evidence.setdefault("deployment_metadata", {})[name] = {
            "depends_on": list(entry.get("depends_on", {})),
            "healthcheck_configured": bool(entry.get("healthcheck")) and not entry.get("healthcheck", {}).get("disable", False),
        }

    def check_url(source, key, target, port):
        raw = services.get(source, {}).get("environment", {}).get(key, "")
        try:
            parsed = urlsplit(raw or "")
            matches = parsed.scheme == "http" and parsed.hostname == target and parsed.port == port
        except ValueError:
            matches = False
        add(f"{source}.{key} -> {target}:{port}", matches, "target matches" if matches else "missing or mismatched target")

    check_url(backend, settings["database_url_key"], database, settings["database_port"])
    check_url("shared-gateway", settings["gateway_url_key"], backend, backend_port)
    for source, target in (("shared-frontend", frontend), ("shared-frontend", "shared-gateway"), ("shared-gateway", backend), (backend, database)):
        common = set(services.get(source, {}).get("networks", {})) & set(services.get(target, {}).get("networks", {}))
        add(f"Configured shared network: {source} -> {target}", bool(common), sorted(common))
    database_path = PurePosixPath(service_config["container_db_path"])
    volumes = services.get(database, {}).get("volumes", [])
    persistent = []
    for volume in volumes:
        if isinstance(volume, dict) and volume.get("target"):
            target = PurePosixPath(volume["target"])
            if target.is_absolute() and target in database_path.parents and volume.get("type") in ("volume", "bind") and not volume.get("read_only", False):
                if volume.get("type") == "bind" or volume.get("source") in config.get("volumes", {}):
                    persistent.append({"type": volume["type"], "target": str(target)})
    add("Configured persistent writable mount covers DB path", bool(persistent), persistent)
    effective_path = services.get(database, {}).get("environment", {}).get("DATABASE_PATH")
    if effective_path is not None:
        add("Configured DATABASE_PATH matches DB collector", effective_path == str(database_path), "matches" if effective_path == str(database_path) else "mismatch")
    else:
        evidence["not_verified"].append("Database default path when DATABASE_PATH is unset")

    homepage = root / "shared/frontend/index.html"
    nginx = root / "shared/frontend/nginx.conf"
    if homepage.is_file():
        links = re.findall(r'href\s*=\s*["\']([^"\']+)["\']', homepage.read_text(encoding="utf-8"))
        add("Shared homepage feature link", settings["home_link"] in links, settings["home_link"])
    if nginx.is_file():
        text = re.sub(r"#[^\n]*", "", nginx.read_text(encoding="utf-8"))
        blocks = re.findall(r"location\s+(?:=\s+)?([^\s{]+)\s*\{([^{}]*)\}", text)
        for location, target, port in [(settings["proxy_location"], frontend, settings["frontend_port"]), ("/api/", "shared-gateway", 5000)]:
            destinations = [match for path, body in blocks if path == location for match in re.findall(r"proxy_pass\s+([^;\s]+)", body)]
            expected = f"http://{target}:{port}"
            add(f"Nginx proxy: {location}", any(url.rstrip("/") == expected for url in destinations), expected)
    evidence["configuration_status"] = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS"
    containers = snapshot.get("containers")
    if containers is None:
        evidence["runtime_status"] = "UNAVAILABLE"
        evidence["runtime_error"] = snapshot.get("runtime_error", "Runtime unavailable")
    else:
        for name in (frontend, backend, database, "shared-frontend", "shared-gateway"):
            instances = [item for item in containers if item.get("Service") == name]
            state = [{"state": item.get("State"), "health": item.get("Health") or "not reported"} for item in instances]
            healthy = bool(instances) and all(item.get("State") == "running" and item.get("Health", "") in ("", None, "healthy") for item in instances)
            configured_health = services.get(name, {}).get("healthcheck", {})
            missing_health = bool(configured_health) and not configured_health.get("disable", False) and any(not item.get("Health") for item in instances)
            status = "FAIL" if not healthy else "PARTIAL" if missing_health else "PASS"
            evidence["runtime"].append({"service": name, "status": status, "observed": state})
        statuses = {item["status"] for item in evidence["runtime"]}
        evidence["runtime_status"] = "FAIL" if "FAIL" in statuses else "PARTIAL" if "PARTIAL" in statuses else "PASS"
    evidence["validation_status"] = (
        "FAIL" if "FAIL" in (evidence["configuration_status"], evidence["runtime_status"]) else
        "PARTIAL" if evidence["runtime_status"] in ("UNAVAILABLE", "PARTIAL") else "PASS"
    )
    return True, evidence
