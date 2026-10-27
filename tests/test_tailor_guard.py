from jobhunt.tailor import shared_keywords, check_no_invention

MASTER = """
Python, PyTorch, LangChain. Built a RAG chatbot with FAISS and the OpenAI API.
Machine Learning, NLP, LLMs, Transformers, LoRA fine-tuning. Docker, Git, Flask.
"""


def test_shared_keywords_must_be_in_master():
    jd = "We use Python, Go, Kubernetes and LangChain for LLM systems."
    shared = shared_keywords(MASTER, jd)
    assert "Python" in shared and "LangChain" in shared
    assert "Go" not in shared and "Kubernetes" not in shared


def test_invention_is_caught():
    tailored = "Experienced with Python and TensorFlow and SQL."
    violations = check_no_invention(MASTER, tailored)
    assert "TensorFlow" in violations and "SQL" in violations


def test_clean_output_passes():
    tailored = "Built RAG systems in Python with LangChain and FAISS."
    assert check_no_invention(MASTER, tailored) == []
