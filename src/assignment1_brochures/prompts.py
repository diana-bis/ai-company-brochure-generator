
LINK_SYSTEM_PROMPT = """
You are selecting relevant pages from a company's website.

Your goal is to identify pages that provide useful information
for two audiences:
1. Potential customers.
2. Potential job candidates.

Selection rules:
- Select up to 3 additional pages.
- Select only URLs from the provided candidate list.
- Do not select the homepage.
- Do not select privacy policies or terms of service.
- Do not select email links or external websites.
- Prefer pages about products, services, company information,
  technology, careers, teams, and company culture.
- Choose pages that provide useful information for one or
  both target audiences.
- Prefer diversity of information. Avoid selecting multiple pages
  that substantially cover the same subject.

For every selected page, provide:
- type: A short description of the page category.
- url: The complete selected URL.
- reason: A clear explanation of why the page is relevant
  to potential customers and/or job candidates.

The reason must explain the actual value of the page,
not simply repeat its title.

Return ONLY a JSON object using this structure:

{
    "links": [
        {
            "type": "products",
            "url": "https://company.example/products",
            "reason": "Explains the company's products and helps potential customers understand its solutions."
        }
    ]
}

All three fields must be non-empty strings.

If no suitable pages exist, return:
{
    "links": []
}
"""


def build_link_selection_prompt(url, candidate_links):
    return f"""
Here are the candidate links collected from the company website:
{url}

Select relevant pages for potential customers and job candidates.

Use only the following normalized candidate URLs:

""" + "\n".join(candidate_links)


# --------------------------------------------------
# Brochure generation prompt
# --------------------------------------------------

def build_brochure_prompt(company_name, audience, context):

    if audience == "customers":
        audience_instructions = """
        Write for potential customers.

        Focus on:
        - The problem the company aims to solve.
        - Its products and services.
        - Practical use cases.
        - Target audiences.
        - What potential customers should clarify before contacting the company.
        """

    elif audience == "candidates":
        audience_instructions = """
        Write for potential job candidates.

        Focus on:
        - The company's business activities.
        - Published roles and teams.
        - Work environment and company culture,
          only when supported by the sources.
        - The application process, if described.
        - What candidates should clarify before applying.
        """

    else:
        raise ValueError("Audience must be 'customers' or 'candidates'")

    prompt = f"""
You are writing a company brochure in Hebrew.

COMPANY:
{company_name}

TARGET AUDIENCE:
{audience}

INSTRUCTIONS:
{audience_instructions}

GENERAL REQUIREMENTS:

1. Write between 200 and 300 words.
   Count the words using Python's split() method.
   The source list at the end is excluded from the count.

2. Use clear Markdown headings and an organized structure.

3. Support every substantial factual claim with a source
   reference in this format: [A1], [A2], etc.

4. Only reference source IDs included in the supplied context.

5. Do not invent customers, prices, job openings,
   employment conditions or company promises.

6. Attribute marketing claims to the company that published them.

7. If important information is unavailable, write:
   "לא נמצא במקורות שנמסרו למודל".

8. Keep company facts consistent across audiences.
   Adapt the structure and emphasis to the reader,
   not the underlying facts.

9. Finish with a section titled "מקורות" containing
   the source IDs and URLs used.

SOURCE MATERIAL:
----------------
{context}
----------------

Write the complete brochure in Hebrew.
"""

    return prompt


# --------------------------------------------------
# Company comparison prompt
# --------------------------------------------------

COMPARISON_DIMENSIONS = [
    "Products and services",
    "Target customers",
    "AI and computing capabilities",
    "Careers and work environment",
]


def build_comparison_prompt(context):

    dimensions = "\n".join(
        f"{i + 1}. {dimension}"
        for i, dimension in enumerate(COMPARISON_DIMENSIONS)
    )

    prompt = f"""
You are an expert business analyst.

Your task is to compare NVIDIA and AMD using only
the supplied company source material.

Write the comparison in Hebrew.

COMPANIES:
- NVIDIA
- AMD

COMPARISON DIMENSIONS:
{dimensions}

INSTRUCTIONS:

1. Create a Markdown comparison table with three columns:
   - Dimension
   - NVIDIA
   - AMD

2. Compare both companies across all four predefined
   dimensions.

3. Support every substantial factual claim with source
   citations using the exact source IDs provided,
   for example [A1] or [B2].

4. Use only information contained in the supplied context.

5. If information is unavailable for a company or dimension,
   explicitly write:
   "לא נמצא במקורות שנמסרו למודל".

6. Do not invent products, prices, customers, job openings,
   employee benefits or company promises.

7. Attribute marketing claims to the company that published them.

8. Only describe differences when the supplied sources
   provide a reasonable basis for comparison.

9. Do not interpret more detailed website information
   as proof that one company is better than the other.

10. After the table, write a concluding paragraph explaining:
    - What needs or customers each company may suit.
    - What additional information should be clarified
      before making a decision.
    - The limitations of comparing companies using
      their own published information.

11. Finish with a source list containing the source IDs
    and their corresponding URLs from the supplied context.

12. Do not introduce information from external knowledge.

SOURCE MATERIAL:
----------------------------------------
{context}
----------------------------------------

Produce a balanced, evidence-based comparison.
"""

    return prompt


# --------------------------------------------------
# Baseline experiment prompt
# --------------------------------------------------

def build_baseline_prompt(company_name, audience, context):

    prompt = f"""
Write a company brochure in Hebrew about {company_name}.

Target audience: {audience}

Use the supplied company information to write
a clear and informative brochure.

Requirements:
- Write 200–300 words, excluding the source list.
- Include an introduction and relevant sections.
- Explain the company's activities and products.
- Adapt the content to the target audience.
- Use factual information from the supplied sources.
- Cite factual claims using source IDs such as [A1].
- Do not invent information.
- Mention when information is unavailable.
- Include a sources section with source IDs and URLs.

Company information:
--------------------
{context}
--------------------

Write the complete brochure in Hebrew.
"""
    return prompt
