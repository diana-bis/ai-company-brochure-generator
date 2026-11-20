
import json

from pathlib import Path


CONTEXT_TEXT_BUDGET = 12000


def build_context(
    sources,
    text_budget=CONTEXT_TEXT_BUDGET,
    output_name="company"
):
    """
    Build a context from saved source records.

    The complete context, including source metadata,
    must stay within the character budget.
    Only successfully collected sources are used.
    """

    if text_budget < 0:
        raise ValueError("text_budget must be non-negative")

    valid_sources = [
        source for source in sources
        if source["status"] == "ok" and source["text"].strip()
    ]

    omitted_sources = [
        source for source in sources
        if source not in valid_sources
    ]

    context_parts = []
    included = []
    truncated = []

    metadata_parts = []

    for source in valid_sources:
        metadata = (
            f"## Source {source['source_id']}\n"
            f"Title: {source['title']}\n"
            f"URL: {source['url']}\n"
            f"Content:\n"
        )
        metadata_parts.append(metadata)

    metadata_cost = sum(len(part) for part in metadata_parts)
    separator_cost = max(0, len(valid_sources) - 1) * 2

    # A source header must not be cut midway.
    if metadata_cost + separator_cost > text_budget:
        raise ValueError(
            "Context budget is too small for source metadata"
        )

    available_text_budget = (
        text_budget - metadata_cost - separator_cost
    )

    source_limit = (
        available_text_budget // len(valid_sources)
        if valid_sources else 0
    )

    for source, metadata in zip(valid_sources, metadata_parts):
        original_text = source["text"]
        selected_text = original_text[:source_limit]

        context_parts.append(metadata + selected_text)
        included.append(source["source_id"])

        if len(selected_text) < len(original_text):
            truncated.append({
                "source_id": source["source_id"],
                "original_characters": len(original_text),
                "included_characters": len(selected_text),
                "reason": "Complete context budget allocation"
            })

    context = "\n\n".join(context_parts)

    manifest = {
        "output_name": output_name,
        "text_budget": text_budget,
        "characters_used": len(context),
        "included_sources": included,
        "truncated_sources": truncated,
        "omitted_sources": [
            {
                "source_id": source["source_id"],
                "reason": f"Source status: {source['status']}"
            }
            for source in omitted_sources
        ]
    }

    output_dir = Path("data/contexts")
    output_dir.mkdir(parents=True, exist_ok=True)

    context_path = output_dir / f"{output_name}_context.txt"
    manifest_path = output_dir / f"{output_name}_manifest.json"

    context_path.write_text(
        context,
        encoding="utf-8"
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(f"Context created: {output_name}")
    print(
        f"Characters used: "
        f"{manifest['characters_used']}/{text_budget}"
    )
    print(f"Included sources: {included}")
    print(f"Truncated sources: {len(truncated)}")
    print(f"Omitted sources: {len(omitted_sources)}")

    return context, manifest
