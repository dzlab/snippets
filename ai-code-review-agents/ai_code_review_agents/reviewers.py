"""Reviewer implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI


DEFAULT_REVIEW_PROMPT = """You are a code security reviewer.
Review code changes and identify security vulnerabilities, bugs, and critical issues.

PR Title: {title}

{task_section}

Code Changes:
{diff}

{context_section}

{instructions}

For each issue found, respond in this exact format:

ISSUE: <brief description>
SEVERITY: <high|medium|low>

Focus on actual vulnerabilities, bugs, and requirement violations.
Avoid minor style comments."""


SECURITY_AGENT_PROMPT = """You are a security expert.
Your only focus is finding security vulnerabilities in code changes.

PR Title: {title}

{task_section}

Code Changes:
{diff}

{context_section}

Security analysis checklist:
- SQL injection through string-built queries.
- XSS through unescaped user-controlled content.
- Authentication bypass.
- Missing authorization checks.
- Hardcoded secrets or credentials.
- Weak randomness or weak cryptography.
- Path traversal.
- Insecure deserialization.
- CORS misconfiguration.
- Timing attacks in secret comparison.
- Open redirects.
- Information disclosure.
- Sensitive data in logs.

For each security vulnerability found, respond exactly as:

ISSUE: <brief security issue>
SEVERITY: <high|medium|low>

Report only real security vulnerabilities and missing required security controls."""


PATTERN_AGENT_PROMPT = """You are a codebase pattern compliance reviewer.
Your only focus is finding violations of task requirements and established codebase patterns.

PR Title: {title}

{task_section}

Code Changes:
{diff}

{context_section}

Pattern analysis checklist:
- Authentication and authorization patterns.
- Parameterized database query patterns.
- Error handling and logging patterns.
- Input validation patterns.
- Secrets management patterns.
- Transaction and locking patterns.
- Rate limiting patterns.
- Safe file path construction.

For each pattern violation found, respond exactly as:

ISSUE: <brief pattern violation>
SEVERITY: <high|medium|low>

Report only task requirement violations or deviations from established codebase patterns."""


def parse_findings(content: str) -> list[dict]:
    findings = []
    current_issue = None

    for raw_line in content.strip().splitlines():
        line = raw_line.strip().replace("###", "").replace("**", "").strip()
        upper = line.upper()

        if upper.startswith("ISSUE:"):
            current_issue = line[6:].strip()
        elif upper.startswith("SEVERITY:") and current_issue:
            findings.append({
                "issue": current_issue,
                "severity": line[9:].strip().lower(),
            })
            current_issue = None

    return findings


def review(
    pr: dict,
    openai_client: "OpenAI",
    model: str = "gpt-4o-mini",
    context: str | None = None,
    task_context: str | None = None,
    custom_prompt: str | None = None,
) -> dict:
    has_context = bool(context and context.strip())
    has_task = bool(task_context and task_context.strip())

    task_section = f"TASK REQUIREMENTS:\n{task_context}" if has_task else ""
    context_section = (
        "EXISTING CODEBASE PATTERNS:\n"
        f"{context}"
        if has_context else ""
    )

    if has_context and has_task:
        instructions = """Review process:
1. Read the task requirements.
2. Study the existing codebase patterns.
3. Compare the new code against both.
4. Report missing requirements and pattern violations.
5. Focus on auth, authorization, SQL, secrets, validation, rate limits, and error handling."""
    elif has_context:
        instructions = """Review process:
1. Study the existing codebase patterns.
2. Compare the new code against those patterns.
3. Report security and reliability deviations."""
    else:
        instructions = "Review only what is visible in the code changes."

    prompt_template = custom_prompt or DEFAULT_REVIEW_PROMPT
    prompt = prompt_template.format(
        title=pr["title"],
        diff=pr["diff"],
        task_section=task_section,
        context_section=context_section,
        instructions=instructions,
    )

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert code reviewer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=800,
    )

    content = response.choices[0].message.content
    return {
        "pr_id": pr["id"],
        "approach": "context-aware" if has_context else "diff-only",
        "findings": parse_findings(content),
        "raw": content,
    }


def review_security(pr: dict, openai_client: "OpenAI", model: str, context: str, task_context: str) -> dict:
    result = review(
        pr,
        openai_client=openai_client,
        model=model,
        context=context,
        task_context=task_context,
        custom_prompt=SECURITY_AGENT_PROMPT,
    )
    result["agent"] = "security"
    return result


def review_pattern(pr: dict, openai_client: "OpenAI", model: str, context: str, task_context: str) -> dict:
    result = review(
        pr,
        openai_client=openai_client,
        model=model,
        context=context,
        task_context=task_context,
        custom_prompt=PATTERN_AGENT_PROMPT,
    )
    result["agent"] = "pattern"
    return result


def keywords(text: str) -> set[str]:
    normalized = (
        text.lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(".", " ")
        .replace(",", " ")
    )
    return {word for word in normalized.split() if len(word) > 3}


def word_overlap(left: str, right: str) -> float:
    left_words = keywords(left)
    right_words = keywords(right)
    if not left_words or not right_words:
        return 0.0
    return len(left_words & right_words) / max(len(left_words), len(right_words))


def already_covered(finding: dict, existing: list[dict], threshold: float = 0.50) -> bool:
    return any(
        word_overlap(finding["issue"], item["issue"]) >= threshold
        for item in existing
    )


def deduplicate_findings(findings: list[dict]) -> list[dict]:
    unique = []
    for finding in findings:
        if finding.get("severity") not in {"high", "medium"}:
            continue
        if not already_covered(finding, unique):
            unique.append(finding)
    return unique


def review_ensemble(
    pr: dict,
    openai_client: "OpenAI",
    model: str,
    context: str,
    task_context: str,
) -> dict:
    security_review = review_security(pr, openai_client, model, context, task_context)
    pattern_review = review_pattern(pr, openai_client, model, context, task_context)

    agreed = []
    for sec in security_review["findings"]:
        for pat in pattern_review["findings"]:
            if word_overlap(sec["issue"], pat["issue"]) > 0.40:
                agreed.append(sec if len(sec["issue"]) >= len(pat["issue"]) else pat)
                break

    # Add one strong unique finding from each specialist as a recall safety net.
    for findings in (security_review["findings"], pattern_review["findings"]):
        for finding in findings:
            if finding.get("severity") in {"high", "medium"} and not already_covered(finding, agreed):
                agreed.append(finding)
                break

    return {
        "pr_id": pr["id"],
        "agent": "ensemble",
        "findings": deduplicate_findings(agreed),
        "security_count": len(security_review["findings"]),
        "pattern_count": len(pattern_review["findings"]),
    }
