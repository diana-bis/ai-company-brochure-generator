
import json
import time

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .config import MODEL, openai
from .logging_utils import log_operation
from .prompts import build_brochure_prompt


def process_stream_events(stream, on_update=None):
    """
    Process streaming events and preserve accumulated text.

    Returns:
        {
            "text": str,
            "status": "completed" | "partial",
            "error": str | None
        }
    """
    accumulated_text = ""
    completed = False
    error_message = None

    try:
        for chunk in stream:
            if chunk is None:
                continue

            choices = getattr(chunk, "choices", None)

            if not choices:
                continue

            choice = choices[0]
            delta = getattr(choice, "delta", None)

            if delta is not None:
                content = getattr(delta, "content", None)

                if isinstance(content, str) and content:
                    accumulated_text += content

                    if on_update:
                        on_update(accumulated_text)

            if getattr(choice, "finish_reason", None) == "stop":
                completed = True

    except Exception as error:
        error_message = str(error)

    return {
        "text": accumulated_text,
        "status": "completed" if completed else "partial",
        "error": error_message,
    }


def generate_brochure_stream(
    company_name,
    context,
    audience,
    on_update=None,
    *,
    company_id=None,
    context_paths=(),
):
    """
    Generate a brochure using streaming.

    The on_update callback is optional:
    - In Jupyter, it can update a Markdown display.
    - In scripts, it can print progress or update another UI.
    """
    run_id = str(uuid4())
    start_time = time.perf_counter()

    brochure = ""
    status = "failure"
    error_message = None
    token_usage = None
    api_calls = 0

    prompt_path = None
    output_path = None
    metadata_path = None

    print(f"Generating {company_name} brochure for {audience}...")

    try:
        prompt = build_brochure_prompt(
            company_name, audience, context
        )

        prompt_dir = Path("data/prompts")
        prompt_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = prompt_dir / f"streaming_{run_id}.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        def tracked_update(text):
            nonlocal brochure
            brochure = text

            if on_update is not None:
                on_update(text)

        api_calls += 1

        stream = openai.with_options(
            max_retries=0
        ).chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True,
            stream_options={"include_usage": True},
        )

        def tracked_stream():
            nonlocal token_usage

            for event in stream:
                usage = getattr(event, "usage", None)

                if usage is not None and hasattr(usage, "model_dump"):
                    token_usage = usage.model_dump(exclude_none=True)

                yield event

        result = process_stream_events(
            tracked_stream(),
            on_update=tracked_update,
        )

        brochure = result["text"]
        status = result["status"]
        error_message = result["error"]

    except Exception as error:
        error_message = str(error)
        status = "partial" if brochure else "failure"

    finally:
        duration = round(time.perf_counter() - start_time, 2)

        output_dir = Path("outputs/streaming")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / (
            f"{company_id or company_name}_{audience}_{run_id}.md"
        )
        output_path.write_text(brochure, encoding="utf-8")

        metadata = {
            "run_id": run_id,
            "company": company_name,
            "audience": audience,
            "model": MODEL,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "status": status,
            "output_path": str(output_path),
            "characters": len(brochure),
            "error": error_message,
            "token_usage": token_usage,
        }

        metadata_path = output_dir / f"{run_id}_metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

        log_operation(
            run_id=run_id,
            operation="streaming_brochure_generation",
            company=company_name,
            audience=audience,
            model=MODEL,
            duration_seconds=duration,
            status=status,
            input_paths=[
                str(path)
                for path in (prompt_path, *context_paths)
                if path is not None and path.is_file()
            ],
            output_paths=[
                str(output_path),
                str(metadata_path),
            ],
            error=error_message,
            token_usage=token_usage,
            api_calls=api_calls,
            http_requests=0,
        )

    print("\nStreaming finished.")
    print("Status:", status)
    print("Run ID:", run_id)
    print("Duration:", duration, "seconds")
    print("Saved to:", output_path)
    print("Metadata saved to:", metadata_path)

    return brochure, status
