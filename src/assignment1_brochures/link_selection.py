
import json
import time

from pathlib import Path
from urllib import response
from uuid import uuid4
from urllib.parse import urljoin, urldefrag, urlsplit

from .config import MODEL, openai
from .logging_utils import log_operation
from .scraping import fetch_website_links

from .prompts import LINK_SYSTEM_PROMPT, build_link_selection_prompt


def normalize_candidate_links(base_url, raw_links):
    base_parts = urlsplit(base_url)

    if base_parts.scheme not in {"http", "https"} or not base_parts.hostname:
        raise ValueError("Invalid company website URL")

    base_host = base_parts.hostname.lower().removeprefix("www.")

    normalized_links = []
    seen = set()

    for link in raw_links:
        if not isinstance(link, str) or not link.strip():
            continue

        absolute_url = urldefrag(
            urljoin(base_url, link.strip())
        ).url

        parts = urlsplit(absolute_url)

        if parts.scheme.lower() not in {"http", "https"}:
            continue

        if not parts.hostname:
            continue

        candidate_host = parts.hostname.lower().removeprefix("www.")

        if candidate_host != base_host:
            continue

        dedupe_key = (
            parts.scheme.lower(),
            candidate_host,
            parts.port,
            parts.path or "/",
            parts.query
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        normalized_links.append(absolute_url)

    return normalized_links


def get_links_user_prompt(url, candidate_links=None):
    if candidate_links is None:
        raw_links = fetch_website_links(url)
        candidate_links = normalize_candidate_links(url, raw_links)

    return build_link_selection_prompt(url, candidate_links)


def validate_link_selection(raw_text, base_url, candidate_links):
    """
    Reject the entire selection if any link is invalid.
    """
    if not raw_text:
        raise ValueError("Empty model response")

    try:
        selected = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"Malformed JSON: {error}") from error

    if not isinstance(selected, dict):
        raise ValueError("Response must be a JSON object")

    links = selected.get("links")

    if not isinstance(links, list):
        raise ValueError("Response must contain a links list")

    if len(links) > 3:
        raise ValueError("More than 3 additional pages selected")

    seen_urls = set()
    validated_links = []

    for index, link in enumerate(links):
        if not isinstance(link, dict):
            raise ValueError(f"Link {index} must be an object")

        for field in ("type", "url", "reason"):
            if not isinstance(link.get(field), str) or not link[field].strip():
                raise ValueError(
                    f"Link {index} has a missing or empty '{field}' field"
                )

        selected_url = link["url"].strip()

        normalized_url = urldefrag(
            urljoin(base_url, selected_url)
        ).url

        if normalized_url not in candidate_links:
            raise ValueError(
                f"URL not in candidate list: {selected_url}"
            )

        if normalized_url in seen_urls:
            raise ValueError(
                f"Duplicate URL: {normalized_url}"
            )

        if normalized_url.rstrip("/") == base_url.rstrip("/"):
            raise ValueError(
                "Homepage cannot be selected as an additional page"
            )

        path = urlsplit(normalized_url).path.lower()

        forbidden_segments = {
            "privacy",
            "privacy-policy",
            "terms",
            "terms-of-use",
            "terms-and-conditions",
        }

        if any(
            segment in forbidden_segments
            for segment in path.split("/")
        ):
            raise ValueError(
                f"Forbidden page selected: {normalized_url}"
            )

        seen_urls.add(normalized_url)

        validated_links.append({
            "type": link["type"].strip(),
            "url": normalized_url,
            "reason": link["reason"].strip(),
        })

    return {"links": validated_links}


def select_relevant_links(url):
    """
    Fetch homepage links, ask Gemini to select pages,
    validate the response, and log the execution.
    """
    run_id = str(uuid4())
    start_time = time.perf_counter()

    api_calls = 0
    http_requests = 0
    token_usage = None
    status = "failure"
    error_message = None

    prompt_path = None
    response_path = None
    rejection_path = None
    raw_text = None
    candidate_links = []

    try:
        http_requests += 1
        raw_links = fetch_website_links(url)

        candidate_links = normalize_candidate_links(
            url, raw_links
        )

        user_prompt = get_links_user_prompt(
            url, candidate_links
        )

        prompt_dir = Path("data/prompts")
        prompt_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = prompt_dir / f"link_selection_{run_id}.json"

        prompt_data = {
            "run_id": run_id,
            "company_url": url,
            "model": MODEL,
            "system_prompt": LINK_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "candidate_links": candidate_links,
        }

        prompt_path.write_text(
            json.dumps(prompt_data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

        api_calls += 1

        response = openai.with_options(
            max_retries=0
        ).chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": LINK_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        usage = getattr(response, "usage", None)

        if usage is not None and hasattr(usage, "model_dump"):
            token_usage = usage.model_dump(exclude_none=True)

        if not response.choices:
            raise ValueError("Gemini returned no response choices")

        raw_text = response.choices[0].message.content

        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ValueError("Gemini returned an empty response")

        response_dir = Path("data/responses")
        response_dir.mkdir(parents=True, exist_ok=True)

        response_path = response_dir / f"link_selection_{run_id}.txt"
        response_path.write_text(
            raw_text if isinstance(raw_text, str) else "",
            encoding="utf-8"
        )

        selected = validate_link_selection(
            raw_text, url, candidate_links
        )

        status = "success"
        print("Gemini selection validated successfully.")
        return selected

    except Exception as error:
        error_message = str(error)

        if isinstance(error, ValueError):
            rejection_dir = Path("logs/link_rejections")
            rejection_dir.mkdir(parents=True, exist_ok=True)

            rejection_path = (
                rejection_dir / f"link_selection_{run_id}.json"
            )

            rejection_path.write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "company_url": url,
                        "raw_response": raw_text,
                        "candidate_links": candidate_links,
                        "rejection_reason": error_message,
                    },
                    indent=4,
                    ensure_ascii=False,
                ),
                encoding="utf-8"
            )

        raise

    finally:
        duration = round(
            time.perf_counter() - start_time, 2
        )

        log_operation(
            run_id=run_id,
            operation="link_selection",
            company=url,
            model=MODEL,
            duration_seconds=duration,
            status=status,
            input_paths=[
                str(path)
                for path in [prompt_path]
                if path is not None and path.is_file()
            ],
            output_paths=[
                str(path)
                for path in [response_path, rejection_path]
                if path is not None and path.is_file()
            ],
            error=error_message,
            token_usage=token_usage,
            api_calls=api_calls,
            http_requests=http_requests,
        )
