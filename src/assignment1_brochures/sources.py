
import json
import time

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .logging_utils import log_operation
from .scraping import fetch_website_contents


def fetch_company_sources(company_id, url, selected):
    """
    Fetch the homepage and selected pages, save source records,
    and log HTTP request attempts and execution results.
    """

    run_id = str(uuid4())
    start_time = time.perf_counter()

    source_prefix = company_id.upper()

    pages = [{"url": url, "type": "homepage"}]

    for link in selected["links"]:
        pages.append({
            "url": link["url"],
            "type": link["type"]
        })

    sources = []
    http_requests = 0
    error_messages = []
    output_path = None

    try:
        for index, page_info in enumerate(pages, start=1):
            source_id = f"{source_prefix}{index}"
            page_url = page_info["url"]

            print(f"Fetching {source_id}: {page_url}")

            source = {
                "source_id": source_id,
                "company_id": source_prefix,
                "url": page_url,
                "title": "",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "text": "",
                "status": "failed"
            }

            try:
                http_requests += 1

                content = fetch_website_contents(page_url)

                if content:
                    title, separator, text = content.partition("\n\n")

                    source["title"] = title.strip()
                    source["text"] = text.strip() if separator else ""

                    source["status"] = (
                        "ok" if source["text"] else "empty"
                    )
                else:
                    source["status"] = "empty"

            except Exception as error:
                error_messages.append(
                    f"{source_id}: {error}"
                )
                print(f"Failed to fetch {source_id}: {error}")

            sources.append(source)

        output_dir = Path("data/sources")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{source_prefix}_sources.json"

        output_path.write_text(
            json.dumps(sources, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

        print(f"\nSaved {len(sources)} sources to {output_path}")

        return sources

    finally:
        duration = round(time.perf_counter() - start_time, 2)

        ok_count = sum(
            source["status"] == "ok" for source in sources
        )

        if not sources or ok_count == 0:
            status = "failure"
        elif error_messages or ok_count < len(sources):
            status = "partial"
        else:
            status = "success"

        log_operation(
            run_id=run_id,
            operation="source_fetching",
            company=source_prefix,
            model=None,
            duration_seconds=duration,
            status=status,
            input_paths=[],
            output_paths=(
                [str(output_path)]
                if output_path is not None and output_path.is_file()
                else []
            ),
            error=(
                "; ".join(error_messages)
                if error_messages else None
            ),
            token_usage=None,
            api_calls=0,
            http_requests=http_requests
        )
