
import json
import time

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .config import MODEL, openai
from .logging_utils import log_operation
from .prompts import (
    build_brochure_prompt,
    build_comparison_prompt,
    build_baseline_prompt,
)


def _get_token_usage(response):
    """Return token usage only when reported by the API."""
    usage = getattr(response, "usage", None)

    if usage is not None and hasattr(usage, "model_dump"):
        return usage.model_dump(exclude_none=True)

    return None


def _generate_text(prompt):
    """Make one Gemini request without automatic SDK retries."""
    response = openai.with_options(
        max_retries=0
    ).chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    if not response.choices:
        raise ValueError("Model returned no choices")

    content = response.choices[0].message.content

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Model returned empty content")

    return content, _get_token_usage(response)


def generate_brochure(company_name, context, audience, company_id=None):
    """Generate, save, and log a company brochure."""
    run_id = str(uuid4())
    start_time = time.perf_counter()

    file_prefix = company_id or company_name

    prompt_path = None
    output_path = None
    token_usage = None
    api_calls = 0
    status = "failure"
    error_message = None

    print(f"Generating {company_name} brochure for {audience}...")

    try:
        prompt = build_brochure_prompt(
            company_name, audience, context
        )

        prompt_dir = Path("data/prompts")
        prompt_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = (
            prompt_dir / f"{file_prefix}_{audience}_{run_id}.txt"
        )
        prompt_path.write_text(prompt, encoding="utf-8")

        api_calls += 1
        brochure, token_usage = _generate_text(prompt)

        output_dir = Path("outputs/brochures")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = (
            output_dir / f"{file_prefix}_{audience}_{run_id}.md"
        )
        output_path.write_text(brochure, encoding="utf-8")

        status = "success"
        return brochure

    except Exception as error:
        error_message = str(error)
        raise

    finally:
        duration = round(time.perf_counter() - start_time, 2)

        log_operation(
            run_id=run_id,
            operation="brochure_generation",
            company=company_name,
            audience=audience,
            model=MODEL,
            duration_seconds=duration,
            status=status,
            input_paths=(
                [str(prompt_path)]
                if prompt_path is not None and prompt_path.is_file()
                else []
            ),
            output_paths=(
                [str(output_path)]
                if output_path is not None and output_path.is_file()
                else []
            ),
            error=error_message,
            token_usage=token_usage,
            api_calls=api_calls,
            http_requests=0,
        )


def generate_comparison(context):
    """Generate and log the NVIDIA vs AMD comparison."""
    run_id = str(uuid4())
    start_time = time.perf_counter()

    prompt_path = None
    output_path = None
    metadata_path = None
    token_usage = None
    api_calls = 0
    status = "failure"
    error_message = None

    print("Generating NVIDIA vs AMD comparison...")

    try:
        prompt = build_comparison_prompt(context)

        prompt_dir = Path("data/prompts")
        prompt_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = prompt_dir / f"comparison_{run_id}.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        api_calls += 1
        comparison, token_usage = _generate_text(prompt)

        output_dir = Path("outputs/comparisons")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"NVIDIA_AMD_{run_id}.md"
        output_path.write_text(comparison, encoding="utf-8")

        status = "success"

        return comparison, {
            "run_id": run_id,
            "status": status,
            "output_path": str(output_path),
        }

    except Exception as error:
        error_message = str(error)
        raise

    finally:
        duration = round(time.perf_counter() - start_time, 2)

        output_dir = Path("outputs/comparisons")
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = output_dir / f"{run_id}_metadata.json"

        metadata = {
            "run_id": run_id,
            "action": "company_comparison",
            "companies": ["NVIDIA", "AMD"],
            "model": MODEL,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "status": status,
            "prompt_path": str(prompt_path) if prompt_path else None,
            "output_path": str(output_path) if output_path else None,
            "error": error_message,
            "token_usage": token_usage,
        }

        metadata_path.write_text(
            json.dumps(metadata, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

        log_operation(
            run_id=run_id,
            operation="company_comparison",
            company="NVIDIA, AMD",
            model=MODEL,
            duration_seconds=duration,
            status=status,
            input_paths=(
                [str(prompt_path)]
                if prompt_path is not None and prompt_path.is_file()
                else []
            ),
            output_paths=[
                str(path)
                for path in [output_path, metadata_path]
                if path is not None and path.is_file()
            ],
            error=error_message,
            token_usage=token_usage,
            api_calls=api_calls,
            http_requests=0,
        )


def generate_baseline(company_name, company_id, audience, context):
    """Generate and log a baseline brochure."""
    run_id = str(uuid4())
    start_time = time.perf_counter()

    prompt_path = None
    output_path = None
    token_usage = None
    api_calls = 0
    status = "failure"
    error_message = None

    print(f"Generating {company_name} {audience} baseline...")

    try:
        prompt = build_baseline_prompt(
            company_name, audience, context
        )

        prompt_dir = Path("data/prompts")
        prompt_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = prompt_dir / (
            f"{company_id}_{audience}_baseline_{run_id}.txt"
        )
        prompt_path.write_text(prompt, encoding="utf-8")

        api_calls += 1
        brochure, token_usage = _generate_text(prompt)

        output_dir = Path("outputs/baseline")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / (
            f"{company_id}_{audience}_baseline_{run_id}.md"
        )
        output_path.write_text(brochure, encoding="utf-8")

        status = "success"
        return brochure

    except Exception as error:
        error_message = str(error)
        raise

    finally:
        duration = round(time.perf_counter() - start_time, 2)

        log_operation(
            run_id=run_id,
            operation="baseline_experiment",
            company=company_name,
            audience=audience,
            model=MODEL,
            duration_seconds=duration,
            status=status,
            input_paths=(
                [str(prompt_path)]
                if prompt_path is not None and prompt_path.is_file()
                else []
            ),
            output_paths=(
                [str(output_path)]
                if output_path is not None and output_path.is_file()
                else []
            ),
            error=error_message,
            token_usage=token_usage,
            api_calls=api_calls,
            http_requests=0,
        )
