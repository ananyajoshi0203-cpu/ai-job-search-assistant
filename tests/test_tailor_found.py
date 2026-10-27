from jobhunt.db import Tracker
from jobhunt.models import Job
from jobhunt import crawler


class FakeLLM:
    def __init__(self, *a, **k):
        pass

    def chat(self, prompt):
        return "Python developer. Built RAG systems with LangChain and FAISS."


def test_tailor_found_moves_ready(monkeypatch, tmp_path):
    monkeypatch.setattr("jobhunt.tailor.LLMClient", FakeLLM)
    monkeypatch.setattr(crawler, "is_open", lambda link: (True, "ok"))
    master = tmp_path / "master.md"
    master.write_text("Python, LangChain, FAISS, RAG, LLMs.")
    t = Tracker(tmp_path / "t.db")
    t.add(Job(company="Acme", role="ML Engineer", link="https://example.com/1",
              description="Python role using LangChain and FAISS for RAG systems."))
    config = {"profile": {"master_resume_path": str(master)},
              "llm": {}, "tailoring": {"output_dir": str(tmp_path / "out")}}
    stats = crawler.tailor_found(config, t)
    assert stats["ready"] == 1
    assert t.list(status="Ready to review")[0].company == "Acme"
    t.close()
