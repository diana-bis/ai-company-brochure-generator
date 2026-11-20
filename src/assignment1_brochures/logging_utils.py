
import json
from datetime import datetime, timezone
from pathlib import Path


def log_operation(
    run_id,
    operation,
    company=None,
    audience=None,
    model=None,
    duration_seconds=None,
    status="success",
    input_paths=None,
    output_paths=None,
    token_usage=None,
    api_calls=0,
    http_requests=0,
    error=None,
):
    """Append an execution record to run_log.jsonl."""

    record = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "company": company,
        "audience": audience,
        "operation": operation,
        "model": model,
        "duration_seconds": duration_seconds,
        "status": status,
        "input_paths": input_paths or [],
        "output_paths": output_paths or [],
        "token_usage": token_usage,
        "api_calls": api_calls,
        "http_requests": http_requests,
        "error": error,
    }

    log_path = Path("logs/run_log.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )

    return record
