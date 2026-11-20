
# Baseline vs. Improved Prompt – Comparative Analysis

## 1. Experiment Setup

The purpose of this experiment was to evaluate whether an improved prompt produces a more effective company brochure compared with a simpler baseline prompt.

Both brochures were generated using identical conditions:

- **Company:** NVIDIA
- **Target audience:** Potential customers
- **Language:** Hebrew
- **Model:** Same configured model (`MODEL`)
- **Source context:** Identical NVIDIA context (`nvidia_context`)
- **Required length:** 200–300 words
- **Source requirements:** Same citation format and source-grounding requirements

Only the prompt instructions and requested structure were intentionally changed.

The baseline used general instructions to produce an informative company brochure. The improved prompt included more detailed customer-specific instructions, including the problems the company aims to solve, its products and services, practical use cases, target audiences, and questions customers should clarify before contacting the company.

The experiment used one baseline generation and the existing improved NVIDIA customers brochure, which was generated using streaming.

## 2. Technical Validation

Both brochures satisfied the basic technical requirements.

| Validation | Baseline | Improved |
|---|---|---|
| Word count | 289 | 286 |
| Word count valid | Yes | Yes |
| Citation IDs valid | Yes | Yes |
| Source references | A1–A4 | A1–A4 |
| Generation method | Regular | Streaming |

Both outputs were generated using the same source context, allowing the comparison to focus on the effect of the prompt.

Streaming changes how the output is delivered, rather than the intended brochure content. However, the different response-delivery methods are an additional experimental limitation.

## 3. Evaluation Criteria

The experiment evaluates four criteria required by the assignment:

1. **Factual faithfulness:** Whether factual claims are supported by the supplied source evidence.
2. **Audience adaptation:** Whether the content addresses the needs of potential customers.
3. **Information coverage:** Whether relevant products, applications, target audiences, and missing information are covered.
4. **Clarity:** Whether the brochure is understandable, logically structured, and easy to follow.

Each criterion is assessed using a 0–2 scoring scale.

### 3.1 Scoring Rubric

| Criterion | Score 0 | Score 1 | Score 2 |
|---|---|---|---|
| Factual faithfulness | Unsupported or contradictory claims | Some claims only partially supported | All checked claims supported |
| Audience adaptation | Mostly irrelevant to customers | Partially customer-focused | Clearly focused on customer needs |
| Information coverage | Several important topics missing | Most important topics covered | Relevant topics covered appropriately |
| Clarity | Difficult to follow | Mostly understandable | Clear and well organized |

## 4. Qualitative Comparison

### 4.1 Factual Faithfulness

The baseline included a statement about NVIDIA's commitment to achieving Net Zero:

> אנו מחויבים להפוך את המחשוב לבר-קיימא כדי להשיג אפס פליטות פחמן (Net Zero)

The saved source A3 states:

> Acceleration is the best way to reclaim power and achieve sustainability and net zero.

**Source:** [A3] https://www.nvidia.com/en-eu/about-nvidia/

The source supports a connection between accelerated computing, sustainability, and Net Zero. However, the brochure presents this as a specific NVIDIA commitment to achieving zero carbon emissions, which is stronger than the available evidence.

**Verdict:** Partially supported.

The improved brochure included the claim that Nemotron and quantum computing technologies accelerate scientific discoveries in chemistry and physics.

The saved source A1 states:

> NVIDIA Introduces Nemotron for Science to Accelerate Agentic Discovery

It also mentions:

> agents in life sciences and chemistry.

Separately, A1 references NVIDIA's work on a quantum computing platform.

**Source:** [A1] https://www.nvidia.com/

These sources support NVIDIA's involvement in scientific research, chemistry, and quantum computing. However, the evidence does not explicitly connect Nemotron to physics discoveries or establish the complete relationship described in the improved brochure.

**Verdict:** Partially supported.

**Assessment:** Neither brochure achieved perfect factual faithfulness in the examined examples. The improved prompt did not completely eliminate claims that extended beyond the supporting evidence.

### 4.2 Audience Adaptation

The baseline included a general company introduction and a section titled:

> הצטרפו אלינו

This section described NVIDIA's workplace and employment environment.

Although this information is relevant to job candidates, it is less useful to potential customers evaluating NVIDIA's products and services.

The improved brochure included a section titled:

> מה על הלקוח להבהיר לפני פנייה?

It encouraged potential customers to consider their technological challenges and infrastructure requirements before contacting the company.

This information directly supports customer decision-making.

**Assessment:** The improved brochure demonstrated stronger audience adaptation by focusing on customer needs rather than general company information.

### 4.3 Information Coverage

The baseline covered several NVIDIA technologies, including:

- Vera and high-performance computing
- Nemotron and NeMo
- RTX and DLSS 3
- Omniverse and digital twins
- NVIDIA DRIVE and autonomous driving

This provided relatively detailed coverage of individual technologies.

However, it also included employment-related information that was less relevant to the customer audience.

The improved brochure covered:

- Artificial intelligence solutions
- Data centers and accelerated computing
- Industrial digitalization
- Autonomous vehicles
- Healthcare and scientific research
- Target customer groups
- Questions to consider before contacting NVIDIA

The improved brochure also explicitly identified unavailable information:

> מידע בנוגע למחירים, תנאי התקשרות או הצעות מחיר פרטניות – לא נמצא במקורות שנמסרו למודל.

This helps readers distinguish available information from details that require further investigation.

**Assessment:** Both brochures covered substantial technical information. The improved brochure provided more relevant coverage for potential customers, while the baseline offered additional detail about certain technologies.

The improvement was primarily in the selection and organization of information rather than the total amount of information.

### 4.4 Clarity and Organization

The baseline used general sections such as:

- About NVIDIA
- Our Solutions
- Sustainability
- Join Us

This structure was understandable but resembled a general company overview.

The improved brochure followed a more customer-oriented sequence:

1. Solutions and activities
2. Practical applications
3. Target audiences
4. Questions before contacting NVIDIA
5. Missing information and sources

This organization follows the customer's decision-making process more closely.

**Assessment:** Both brochures were readable and logically structured. The improved version offered a clearer progression for the intended audience.

## 5. Evaluation Results

| Criterion | Baseline | Improved |
|---|---:|---:|
| Factual faithfulness | 1/2 | 1/2 |
| Audience adaptation | 1/2 | 2/2 |
| Information coverage | 1/2 | 2/2 |
| Clarity | 2/2 | 2/2 |
| **Total** | **5/8** | **7/8** |

The scores represent a qualitative evaluation of the inspected outputs rather than an exhaustive verification of every factual claim.

### Interpretation

**Factual faithfulness:** No clear improvement was established. Both brochures included claims that were only partially supported by the available sources.

**Audience adaptation:** The improved prompt produced a more customer-focused brochure, avoiding the baseline's employment-oriented content.

**Information coverage:** The improved version included more decision-relevant information, particularly target audiences, customer requirements, and missing information.

**Clarity:** Both brochures were clear. The improved version had a more useful customer-oriented structure, but this did not justify a higher score on the selected scale.

## 6. Overall Findings

The experiment suggests that a more detailed and audience-specific prompt can improve the relevance, organization, and usefulness of generated brochures.

Both versions passed the word-count and citation-ID validation checks. However, these technical checks did not guarantee factual accuracy.

The source-based evaluation identified limitations in both outputs. In particular, both brochures contained claims that extended beyond what was explicitly established in the saved source material.

The most significant improvements appeared in audience adaptation and information coverage.

The experiment also demonstrated that additional prompt instructions do not necessarily improve every evaluation criterion. For factual faithfulness and clarity, the scores remained unchanged.

Because the experiment involved only one company, one audience, and one generation per prompt, the results should not be interpreted as a general ranking of prompting methods or language models.

## 7. Conclusion

The improved prompt produced a brochure that was better aligned with the needs of potential customers.

The main improvement was not simply a change in writing style, but a change in the structure, relevance, and selection of information presented to the reader.

However, both versions contained partially supported factual claims, demonstrating that prompt engineering alone does not guarantee factual reliability.

The experiment supports using audience-specific instructions together with source validation, explicit missing-information handling, and manual factual auditing when generating company brochures.

