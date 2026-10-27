"""Truthful resume tailoring.

The rule that defines this project: a keyword from a job description may be
used ONLY where the master resume already shows that skill or experience.
Nothing is invented — no skills, tools, projects, metrics, or employers.
The master resume file is never overwritten; every role gets its own file.
"""
from __future__ import annotations
import json
import os
import re

# Skills/tools this tool knows how to recognise in job descriptions.
# Matching is deliberately conservative (whole phrases, case-insensitive).
SKILL_LEXICON = [
    "Python", "SQL", "PyTorch", "TensorFlow", "scikit-learn", "Hugging Face",
    "LangChain", "OpenAI API", "FAISS", "NLP", "Computer Vision", "LLMs",
    "RAG", "Transformers", "LoRA", "Embeddings", "Docker", "AWS", "Git",
    "Linux", "Flask", "Streamlit", "Machine Learning", "Deep Learning",
    "Data Pipelines", "Model Evaluation", "Fine-Tuning", "APIs",
]


def skills_in(text: str) -> set[str]:
    found = set()
    low = text.lower()
    for skill in SKILL_LEXICON:
        if re.search(r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])", low):
            found.add(skill)
    return found


def shared_keywords(master_resume: str, job_description: str) -> list[str]:
    """Keywords the JD asks for AND the master resume already supports.
    These — and only these — may be emphasised in the tailored version."""
    return sorted(skills_in(job_description) & skills_in(master_resume))


def check_no_invention(master_resume: str, tailored: str) -> list[str]:
    """Post-generation guard: known skills that appear in the tailored resume
    but NOT in the master resume. Empty list = pass."""
    return sorted(skills_in(tailored) - skills_in(master_resume))


TAILOR_PROMPT = """You are tailoring a resume for one specific job.

HARD RULES — violating any of these is a failure:
1. Use ONLY facts, skills, tools, projects, employers, titles, dates, schools
   and numbers that appear in the MASTER RESUME below. Invent nothing.
2. You may emphasise ONLY these shared keywords (present in both the job
   description and the master resume): {keywords}
3. Do not change employers, titles, dates, school, or degree.
4. Keep the same sections as the master resume. Reorder sections and bullets
   so the most relevant experience for this job comes first.
5. Reword existing bullets for clarity using the job description's wording
   for things the resume genuinely shows. Keep it to one page.

MASTER RESUME:
{master}

JOB: {company} — {role}
JOB DESCRIPTION:
{jd}

Return only the tailored resume in Markdown."""


class LLMClient:
    """Minimal OpenAI-compatible chat client. Bring your own key."""

    def __init__(self, base_url: str, model: str, api_key_env: str = "OPENAI_API_KEY"):
        import requests
        self._requests = requests
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.key = os.environ.get(api_key_env, "")

    def chat(self, prompt: str) -> str:
        if not self.key:
            raise RuntimeError("No API key: set the env var named in config (llm.api_key_env).")
        r = self._requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={"model": self.model,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def tailor_resume(master_resume: str, company: str, role: str,
                  job_description: str, llm: LLMClient) -> tuple[str, list[str]]:
    """Returns (tailored_markdown, shared_keywords). Raises if the model
    output fails the no-invention check."""
    keywords = shared_keywords(master_resume, job_description)
    prompt = TAILOR_PROMPT.format(keywords=", ".join(keywords) or "(none)",
                                  master=master_resume, company=company,
                                  role=role, jd=job_description[:12000])
    out = llm.chat(prompt)
    violations = check_no_invention(master_resume, out)
    if violations:
        raise ValueError(f"Tailored output failed no-invention check: {violations}")
    return out, keywords
