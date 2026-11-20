
"""
Advanced Company Brochure Generator
===================================

Main entry point for the NVIDIA vs AMD assignment.

Execution modes:
    inspect - Inspect saved sources, contexts and outputs.
    verify  - Validate existing assignment deliverables.
    brochures - Regenerate the four brochures from saved sources.
    full    - Execute the complete live workflow.

Default mode: inspect

Full and brochures modes call Gemini. Only full mode makes website requests.
"""

import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from assignment1_brochures.config import PROJECT_ROOT
from assignment1_brochures.link_selection import select_relevant_links
from assignment1_brochures.sources import fetch_company_sources
from assignment1_brochures.context import build_context
from assignment1_brochures.generation import (
    generate_brochure,
    generate_comparison,
    generate_baseline,
)
from assignment1_brochures.streaming import generate_brochure_stream
from assignment1_brochures.prompts import (
    build_brochure_prompt,
    build_comparison_prompt,
    build_baseline_prompt,
)


COMPANIES = {
    "A": {
        "name": "NVIDIA",
        "url": "https://www.nvidia.com/",
    },
    "B": {
        "name": "AMD",
        "url": "https://www.amd.com/en.html",
    },
}

SOURCE_DIR = PROJECT_ROOT / "data" / "sources"
CONTEXT_DIR = PROJECT_ROOT / "data" / "contexts"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

BROCHURE_DIR = OUTPUT_DIR / "brochures"
COMPARISON_DIR = OUTPUT_DIR / "comparisons"
BASELINE_DIR = OUTPUT_DIR / "baseline"
REPORT_DIR = OUTPUT_DIR / "reports"

BROCHURE_MIN_WORDS = 200
BROCHURE_MAX_WORDS = 300

# Four required brochures.
# NVIDIA customers is the official streamed brochure.
BROCHURE_PATTERNS = {
    ("A", "customers"): "A_customers_streamed_*.md",
    ("A", "candidates"): "A_candidates_*.md",
    ("B", "customers"): "B_customers_*.md",
    ("B", "candidates"): "B_candidates_*.md",
}

CONTEXT_FILES = {
    "A": "NVIDIA_context.txt",
    "B": "AMD_context.txt",
    "comparison": "NVIDIA_AMD_comparison_context.txt",
}


def read_text(path):
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def is_source_heading(line):
    """Recognize source-list headings in common Markdown formats."""
    line = line.strip()

    pattern = (
        r"^(?:#{1,6}\s*)?"
        r"(?:\*\*|__)?"
        r"(?:Sources|References|מקורות|רשימת מקורות)"
        r"(?:\*\*|__)?"
        r"\s*:?\s*$"
    )

    return bool(re.match(pattern, line, flags=re.IGNORECASE))


def load_saved_sources(company_id):
    """Load source records previously collected for a company."""
    path = SOURCE_DIR / f"{company_id}_sources.json"

    if not path.is_file():
        raise FileNotFoundError(
            f"Saved sources not found: {path}"
        )

    data = json.loads(read_text(path))

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a list of source records in {path}"
        )

    return data


def load_saved_context(company_id):
    """Load the exact saved context instead of rebuilding it."""
    filename = CONTEXT_FILES[company_id]
    path = CONTEXT_DIR / filename

    if not path.is_file():
        raise FileNotFoundError(
            f"Saved context not found: {path}"
        )

    return read_text(path)


def latest_matching_file(directory, pattern):
    """Find the most recently modified matching file."""
    matches = list(directory.glob(pattern))

    if not matches:
        return None

    return max(
        matches,
        key=lambda path: path.stat().st_mtime,
    )



def extract_brochure_body(text):
    """
    Exclude the final source/reference list from word counting.
    Supports bold, plain text and Markdown headings.
    """
    lines = text.splitlines()

    for index, line in enumerate(lines):
        if is_source_heading(line):
            return "\n".join(lines[:index])

    return text


def count_words(text):
    """Count whitespace-separated words."""
    return len(text.split())


def validate_brochure(text, source_ids):
    """
    Validate brochure content against core assignment rules.

    Returns:
        (passed, messages)
    """
    messages = []
    body = extract_brochure_body(text)
    word_count = count_words(body)

    if BROCHURE_MIN_WORDS <= word_count <= BROCHURE_MAX_WORDS:
        messages.append(
            f"PASS: {word_count} words (excluding sources)"
        )
    else:
        messages.append(
            f"FAIL: {word_count} words; expected "
            f"{BROCHURE_MIN_WORDS}-{BROCHURE_MAX_WORDS}"
        )

    source_id_pattern = r"\b[A-Z][0-9]+\b"
    cited_ids = {
        source_id
        for bracket in re.findall(r"\[([^\[\]\n]+)\]", text)
        for source_id in re.findall(source_id_pattern, bracket)
    }
    body_has_citation = any(
        re.search(source_id_pattern, bracket)
        for bracket in re.findall(r"\[([^\[\]\n]+)\]", body)
    )
    unknown_ids = cited_ids.difference(source_ids)

    if unknown_ids:
        messages.append(
            "FAIL: Source IDs absent from context: "
            + ", ".join(sorted(unknown_ids))
        )
    elif body_has_citation:
        messages.append(
            "PASS: Cited source IDs belong to the context: "
            + ", ".join(sorted(cited_ids))
        )
    else:
        messages.append(
            "FAIL: No recognized source ID citations in body"
        )

    # Check for a recognizable source list.
    
    has_source_list = any(
        is_source_heading(line)
        for line in text.splitlines()
    )

    if has_source_list:
        messages.append("PASS: Source list heading found")
    else:
        messages.append(
            "FAIL: No recognizable source list heading"
        )


    passed = all(
        message.startswith("PASS")
        for message in messages
    )

    return passed, messages


def inspect_saved_workflow():
    """
    Inspect saved assignment inputs and outputs.

    No API calls, HTTP requests, or file modifications.
    """
    print("\n=== SAVED WORKFLOW INSPECTION ===")

    company_contexts = {}

    for company_id, company in COMPANIES.items():
        sources = load_saved_sources(company_id)
        context = load_saved_context(company_id)
        company_contexts[company_id] = context

        ok_sources = [
            source
            for source in sources
            if source.get("status") == "ok"
        ]

        print(f"\n{company['name']}")
        print(f"  Total sources: {len(sources)}")
        print(f"  Valid sources: {len(ok_sources)}")
        print(f"  Saved context characters: {len(context)}")

        for audience in ("customers", "candidates"):
            prompt = build_brochure_prompt(
                company["name"],
                audience,
                context,
            )

            print(
                f"  {audience} prompt: "
                f"{len(prompt)} characters"
            )

    comparison_context = load_saved_context("comparison")

    comparison_prompt = build_comparison_prompt(
        comparison_context
    )

    baseline_prompt = build_baseline_prompt(
        "NVIDIA",
        "customers",
        company_contexts["A"],
    )

    print("\nComparison")
    print(
        "  Shared context characters:",
        len(comparison_context)
    )
    print(
        "  Comparison prompt characters:",
        len(comparison_prompt)
    )
    print(
        "  Baseline prompt characters:",
        len(baseline_prompt)
    )

    print("\nSaved deliverables")

    for key, pattern in BROCHURE_PATTERNS.items():
        company_id, audience = key

        path = latest_matching_file(
            BROCHURE_DIR,
            pattern,
        )

        label = (
            f"{COMPANIES[company_id]['name']} "
            f"{audience}"
        )

        print(
            f"  {label}: "
            f"{path.name if path else 'MISSING'}"
        )

    comparison_file = latest_matching_file(
        COMPARISON_DIR,
        "NVIDIA_AMD_*.md",
    )

    baseline_file = BASELINE_DIR / (
        "NVIDIA_customers_baseline.md"
    )

    print(
        "  Comparison:",
        comparison_file.name if comparison_file else "MISSING"
    )
    print(
        "  Baseline:",
        baseline_file.name
        if baseline_file.is_file()
        else "MISSING"
    )

    print("\nInspection completed.")
    print("No API calls or website requests.")
    print("No files modified.")


def verify_saved_workflow():
    """
    Verify required saved deliverables and supporting evidence.

    No API calls, HTTP requests, or file modifications.
    """
    print("\n=== ASSIGNMENT VERIFICATION ===")

    failures = []
    source_ids_by_company = {}

    # 1. Source records
    for company_id, company in COMPANIES.items():
        try:
            sources = load_saved_sources(company_id)

            valid_sources = [
                source
                for source in sources
                if source.get("status") == "ok"
                and str(source.get("text", "")).strip()
            ]

            if len(valid_sources) == 4:
                print(
                    f"PASS: {company['name']} has "
                    "4 usable sources"
                )
            else:
                message = (
                    f"{company['name']} has "
                    f"{len(valid_sources)} usable sources; "
                    "expected 4"
                )
                failures.append(message)
                print("FAIL:", message)

        except (OSError, ValueError, KeyError) as error:
            failures.append(str(error))
            print("FAIL:", error)
            source_ids_by_company[company_id] = []

    # 2. Saved contexts and manifests
    for key, filename in CONTEXT_FILES.items():
        context_path = CONTEXT_DIR / filename

        if not context_path.is_file():
            message = f"Missing context: {filename}"
            failures.append(message)
            print("FAIL:", message)
            continue

        content = read_text(context_path)

        if not content.strip():
            message = f"Empty context: {filename}"
            failures.append(message)
            print("FAIL:", message)
        elif len(content) > 12000:
            message = (
                f"Context exceeds 12000 characters: {filename}"
            )
            failures.append(message)
            print("FAIL:", message)
        else:
            print(
                f"PASS: {filename} "
                f"({len(content)} characters)"
            )

        manifest_path = context_path.with_name(
            context_path.stem.replace("_context", "_manifest")
            + ".json"
        )

        try:
            included_ids = json.loads(read_text(manifest_path))["included_sources"]
            if key != "comparison":
                source_ids_by_company[key] = included_ids
            print(f"PASS: {manifest_path.name}")
        except (OSError, ValueError, KeyError) as error:
            message = f"Unable to read {manifest_path.name}: {error}"
            failures.append(message)
            print("FAIL:", message)

    # 3. Four brochures
    print("\nChecking historical citations against saved context manifests.")
    for (company_id, audience), pattern in BROCHURE_PATTERNS.items():
        company_name = COMPANIES[company_id]["name"]

        print(f"\n{company_name} — {audience}")

        brochure_path = latest_matching_file(
            BROCHURE_DIR,
            pattern,
        )

        if brochure_path is None:
            message = (
                f"Missing brochure: {company_name} {audience}"
            )
            failures.append(message)
            print("FAIL:", message)
            continue

        print("File:", brochure_path.name)

        brochure = read_text(brochure_path)

        passed, messages = validate_brochure(
            brochure,
            source_ids_by_company.get(company_id, []),
        )

        for message in messages:
            print(" ", message)

        if not passed:
            failures.append(
                f"Brochure validation failed: "
                f"{company_name} {audience}"
            )

    # 4. Comparison
    comparison_path = latest_matching_file(
        COMPARISON_DIR,
        "NVIDIA_AMD_*.md",
    )

    if comparison_path and read_text(comparison_path).strip():
        print("\nPASS: Comparison exists and is nonempty")
    else:
        message = "Comparison missing or empty"
        failures.append(message)
        print("\nFAIL:", message)

    # 5. Baseline
    baseline_path = (
        BASELINE_DIR / "NVIDIA_customers_baseline.md"
    )

    if baseline_path.is_file() and read_text(baseline_path).strip():
        print("PASS: Baseline exists and is nonempty")
    else:
        message = "Baseline missing or empty"
        failures.append(message)
        print("FAIL:", message)

    # 6. Audit and baseline evaluation
    required_reports = [
        REPORT_DIR / "manual_factual_audit.md",
        REPORT_DIR / "baseline_vs_improved.md",
    ]

    for path in required_reports:
        if path.is_file() and read_text(path).strip():
            print(f"PASS: {path.name}")
        else:
            message = f"Missing or empty report: {path.name}"
            failures.append(message)
            print("FAIL:", message)

    # 7. Run log
    run_log = PROJECT_ROOT / "logs" / "run_log.jsonl"

    if run_log.is_file() and read_text(run_log).strip():
        print("PASS: Execution log exists")
    else:
        message = "Execution log missing or empty"
        failures.append(message)
        print("FAIL:", message)

    print("\n" + "=" * 45)

    if failures:
        print(
            f"VERIFICATION FAILED: "
            f"{len(failures)} issue(s)"
        )

        for failure in failures:
            print(" -", failure)

        return False

    print("VERIFICATION PASSED")
    print("All checked deliverables are present and valid.")
    print("No API calls or website requests.")
    print("No files modified.")

    return True


def generate_company_brochures(companies, company_contexts, company_manifests):
    """Generate and validate two brochures per company, streaming one."""
    for company_id, company in companies.items():
        context = company_contexts[company_id]

        valid_ids = company_manifests[company_id]["included_sources"]
        context_dir = Path("data/contexts")
        context_paths = (
            context_dir / f"{company_id}_context.txt",
            context_dir / f"{company_id}_manifest.json",
        )

        for audience in ("customers", "candidates"):
            print(
                f"\nGenerating {company['name']} "
                f"brochure for {audience}"
            )

            if company_id == "A" and audience == "customers":
                displayed_characters = 0

                def display_update(accumulated_text):
                    nonlocal displayed_characters
                    print(accumulated_text[displayed_characters:], end="", flush=True)
                    displayed_characters = len(accumulated_text)

                brochure, status = generate_brochure_stream(
                    company["name"],
                    context,
                    audience,
                    on_update=display_update,
                    company_id=company_id,
                    context_paths=context_paths,
                )
                print()

                if status != "completed":
                    raise RuntimeError(
                        "Streamed brochure did not complete. "
                        f"Status: {status}"
                    )

            else:
                brochure = generate_brochure(
                    company["name"],
                    context,
                    audience,
                    company_id=company_id,
                    context_paths=context_paths,
                )

            passed, messages = validate_brochure(
                brochure,
                valid_ids,
            )

            for message in messages:
                print(" ", message)

            if not passed:
                raise RuntimeError(
                    f"Invalid generated brochure: "
                    f"{company['name']} {audience}"
                )


def run_full_workflow(companies):
    """
    Execute the complete live assignment workflow.

    WARNING:
    - Makes website requests.
    - Makes Gemini API calls.
    - Generates new outputs.
    - May replace existing saved source/context files.

    Use only when full regeneration is intended.
    """
    company_contexts = {}
    company_manifests = {}
    all_sources = []

    print("\n=== FULL WORKFLOW ===")

    # Step 1-3: Research and evidence collection
    for company_id, company in companies.items():
        print(f"\n=== Processing {company['name']} ===")

        selected = select_relevant_links(company["url"])

        sources = fetch_company_sources(
            company_id,
            company["url"],
            selected,
        )

        context, manifest = build_context(
            sources,
            output_name=company_id,
        )

        company_contexts[company_id] = context
        company_manifests[company_id] = manifest
        all_sources.extend(sources)

        included = manifest.get("included_sources", [])

        print(
            f"Prepared {company['name']}: "
            f"{len(included)} included sources"
        )

    generate_company_brochures(companies, company_contexts, company_manifests)

    # Step 5: Shared-budget comparison
    comparison_context, _ = build_context(
        all_sources,
        output_name="A_B_comparison",
    )

    comparison, comparison_metadata = generate_comparison(
        comparison_context,
        tuple(company["name"] for company in companies.values()),
        output_prefix="A_B",
    )

    if not comparison or not comparison.strip():
        raise RuntimeError(
            "Comparison generation returned empty content"
        )

    if comparison_metadata.get("status") != "success":
        raise RuntimeError(
            "Comparison generation did not succeed"
        )

    print("\nPASS: Comparison generated")

    # Step 6: Baseline experiment
    baseline = generate_baseline(
        companies["A"]["name"],
        "A",
        "customers",
        company_contexts["A"],
    )

    if not baseline or not baseline.strip():
        raise RuntimeError(
            "Baseline generation returned empty content"
        )

    print("PASS: Baseline generated")

    print("\nFull workflow completed successfully.")


def regenerate_saved_brochures():
    """Build fresh, matching contexts and manifests from saved source records."""
    contexts = {}
    manifests = {}
    for company_id in COMPANIES:
        contexts[company_id], manifests[company_id] = build_context(
            load_saved_sources(company_id), output_name=company_id,
        )
        if not manifests[company_id]["included_sources"]:
            raise ValueError(f"Company {company_id} has no usable saved sources.")

    generate_company_brochures(COMPANIES, contexts, manifests)


def run_in_output_directory(workflow, *args):
    run_dir = PROJECT_ROOT / "runs" / str(uuid4())
    run_dir.mkdir(parents=True)
    print(f"Saving this run to {run_dir}")
    previous_dir = Path.cwd()
    try:
        os.chdir(run_dir)
        workflow(*args)
    finally:
        os.chdir(previous_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Company Brochure Generator"
    )

    parser.add_argument(
        "--mode",
        choices=["inspect", "verify", "brochures", "full"],
        default="inspect",
        help="Workflow execution mode",
    )

    for flag in ("--company-a", "--company-b"):
        parser.add_argument(
            flag, nargs=2, metavar=("NAME", "URL"),
            help="Company name and website URL for full mode",
        )

    args = parser.parse_args()

    if args.mode != "full" and (args.company_a or args.company_b):
        parser.error("Company options require --mode full.")

    if args.mode == "inspect":
        inspect_saved_workflow()

    elif args.mode == "verify":
        passed = verify_saved_workflow()

        if not passed:
            raise SystemExit(1)

    elif args.mode == "brochures":
        run_in_output_directory(regenerate_saved_brochures)

    elif args.mode == "full":
        if not args.company_a or not args.company_b:
            parser.error("Full mode requires --company-a NAME URL and --company-b NAME URL.")

        companies = {}
        for company_id, values in (("A", args.company_a), ("B", args.company_b)):
            name, url = (value.strip() for value in values)
            try:
                parsed = urlsplit(url)
                valid_url = (
                    parsed.scheme in {"http", "https"}
                    and bool(parsed.hostname)
                    and parsed.username is None
                    and not any(character.isspace() for character in url)
                )
                parsed.port  # Validate an explicitly supplied port.
            except ValueError:
                valid_url = False
            if not name or not valid_url:
                parser.error(f"Company {company_id} requires a name and a valid HTTP(S) URL.")
            companies[company_id] = {"name": name, "url": url}

        if companies["A"]["name"].casefold() == companies["B"]["name"].casefold():
            parser.error("Enter two distinct company names.")

        print(
            "\nWARNING: Full mode will make live website "
            "and Gemini API requests."
        )

        confirmation = input(
            "\nType RUN FULL to continue: "
        )

        if confirmation != "RUN FULL":
            print("Full workflow cancelled.")
            return

        run_in_output_directory(run_full_workflow, companies)


if __name__ == "__main__":
    main()
