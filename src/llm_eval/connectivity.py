from __future__ import annotations

import re
import os
from dataclasses import dataclass
from urllib import error, request

from llm_eval.config import RunConfig, load_env_file
from llm_eval.providers import InferenceRequest, build_provider_client

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{16,}"),
]


@dataclass(frozen=True)
class ConnectivityResult:
    provider: str
    model: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class KeyDebugInfo:
    env_var: str
    present: bool
    length: int
    starts_with: str
    ends_with: str
    has_whitespace: bool


@dataclass(frozen=True)
class EndpointDiagnostic:
    endpoint: str
    ok: bool
    status_code: int | None
    detail: str


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_KEY]", redacted)
    return redacted


def check_connectivity(config: RunConfig, env_path: str = ".env") -> list[ConnectivityResult]:
    load_env_file(env_path)
    results: list[ConnectivityResult] = []
    for provider_cfg in config.providers:
        try:
            client = build_provider_client(
                provider_config=provider_cfg,
                timeout_seconds=config.policy.reliability.request_timeout_seconds,
            )
            response = client.generate(
                InferenceRequest(
                    prompt="Reply with only the letter A.",
                    temperature=0.0,
                    max_tokens=8,
                )
            )
            detail = f"ok ({len(response.text.strip())} chars)"
            results.append(
                ConnectivityResult(
                    provider=provider_cfg.provider,
                    model=provider_cfg.model,
                    ok=True,
                    detail=detail,
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                ConnectivityResult(
                    provider=provider_cfg.provider,
                    model=provider_cfg.model,
                    ok=False,
                    detail=redact_secrets(str(exc))[:220],
                )
            )
    return results


def get_key_debug_info(env_var: str, env_path: str = ".env") -> KeyDebugInfo:
    """Return safe, masked key metadata for debugging env loading."""
    load_env_file(env_path)
    value = os.getenv(env_var, "")
    present = bool(value)
    stripped = value.strip()
    starts_with = stripped[:7] if stripped else ""
    ends_with = stripped[-4:] if stripped else ""
    has_whitespace = value != stripped or any(ch.isspace() for ch in value)
    return KeyDebugInfo(
        env_var=env_var,
        present=present,
        length=len(stripped),
        starts_with=starts_with,
        ends_with=ends_with,
        has_whitespace=has_whitespace,
    )


def _http_get(url: str, headers: dict[str, str], timeout_seconds: int = 30) -> tuple[int | None, str]:
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def _http_post_json(
    url: str, headers: dict[str, str], payload: dict, timeout_seconds: int = 30
) -> tuple[int | None, str]:
    import json

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        headers={**headers, "Content-Type": "application/json"},
        data=body,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def diagnose_openai_endpoints(
    *,
    env_var: str = "OPENAI_API_KEY",
    model: str = "gpt-4o-mini",
    env_path: str = ".env",
    project_id_env_var: str = "OPENAI_PROJECT_ID",
    organization_id_env_var: str = "OPENAI_ORG_ID",
) -> list[EndpointDiagnostic]:
    load_env_file(env_path)
    key = os.getenv(env_var, "").strip()
    if not key:
        return [
            EndpointDiagnostic(
                endpoint="key_presence",
                ok=False,
                status_code=None,
                detail=f"{env_var} missing",
            )
        ]

    headers = {"Authorization": f"Bearer {key}"}
    project_id = os.getenv(project_id_env_var, "").strip()
    if project_id:
        headers["OpenAI-Project"] = project_id
    organization_id = os.getenv(organization_id_env_var, "").strip()
    if organization_id:
        headers["OpenAI-Organization"] = organization_id
    diagnostics: list[EndpointDiagnostic] = []

    status, body = _http_get("https://api.openai.com/v1/models", headers=headers)
    diagnostics.append(
        EndpointDiagnostic(
            endpoint="GET /v1/models",
            ok=status == 200,
            status_code=status,
            detail=redact_secrets((body or "")[:220].replace("\n", " ")),
        )
    )

    status, body = _http_post_json(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        payload={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with only A."}],
            "max_tokens": 8,
            "temperature": 0,
        },
    )
    diagnostics.append(
        EndpointDiagnostic(
            endpoint="POST /v1/chat/completions",
            ok=status == 200,
            status_code=status,
            detail=redact_secrets((body or "")[:220].replace("\n", " ")),
        )
    )
    return diagnostics
