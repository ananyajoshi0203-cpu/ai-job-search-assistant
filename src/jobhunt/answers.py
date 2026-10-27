"""Draft application answers, generated from the tailored resume ONLY.
Any field the resume doesn't cover is marked 'leave blank' — never filled
with an invention."""
from __future__ import annotations
from .tailor import LLMClient

ANSWERS_PROMPT = """Prepare draft application answers for this job, using ONLY
the tailored resume below. Do not invent facts, skills, metrics, contact
details, or work authorization. If a common field is not covered by the
resume (phone, salary expectations, references), write 'leave blank'.

TAILORED RESUME:
{resume}

JOB: {company} — {role}

Write Markdown with: name, email (only if on the resume), location,
LinkedIn, GitHub (only if on the resume), education summary, and short draft
answers for: 'Describe your experience', 'Describe a relevant project',
'What are your technical skills?'."""


def draft_answers(tailored_resume: str, company: str, role: str,
                  llm: LLMClient) -> str:
    return llm.chat(ANSWERS_PROMPT.format(resume=tailored_resume,
                                          company=company, role=role))
