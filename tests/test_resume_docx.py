import zipfile
from jobhunt.resume_docx import markdown_to_docx


def test_markdown_to_docx_is_valid(tmp_path):
    md = "# ALEX RIVERA\n## PROJECTS\n- Built a **RAG** chatbot with FAISS\nPlain line."
    out = markdown_to_docx(md, tmp_path / "r.docx")
    assert zipfile.is_zipfile(out)
    with zipfile.ZipFile(out) as z:
        xml = z.read("word/document.xml").decode()
    assert "ALEX RIVERA" in xml and "RAG" in xml
    assert "**" not in xml and "##" not in xml
