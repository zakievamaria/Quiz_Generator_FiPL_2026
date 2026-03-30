import pytest

from src.core.document_loader import DocumentLoader


def create_txt_file(tmp_path, name="test.txt", content="bonjour"):
    file_path = tmp_path / name
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def test_fails_with_no_files():
    with pytest.raises(ValueError):
        DocumentLoader([])


def test_fails_with_more_than_10_files(tmp_path):
    paths = []
    for i in range(11):
        paths.append(create_txt_file(tmp_path, f"file{i}.txt"))

    with pytest.raises(ValueError):
        DocumentLoader(paths)


def test_fails_if_file_does_not_exist():
    with pytest.raises(FileNotFoundError):
        DocumentLoader(["non_existent.txt"])


def test_fails_on_unsupported_extension(tmp_path):
    file_path = tmp_path / "file.pdf"
    file_path.write_text("data")

    with pytest.raises(ValueError):
        DocumentLoader([str(file_path)])


def test_set_files_replaces_and_validates(tmp_path):
    file1 = create_txt_file(tmp_path, "a.txt")
    loader = DocumentLoader([file1])

    file2 = create_txt_file(tmp_path, "b.txt")
    loader.set_files([file2])

    assert loader.file_paths == [file2]


def test_load_txt_file(tmp_path):
    content = "Bonjour tout le monde"
    file_path = create_txt_file(tmp_path, "test.txt", content)

    loader = DocumentLoader([file_path])
    docs = loader.load()

    assert len(docs) == 1
    doc = docs[0]

    assert doc["file_path"] == file_path
    assert doc["content"] == content
    assert doc["size"] == len(content)
    assert doc["extension"] == ".txt"


def test_load_multiple_files(tmp_path):
    file1 = create_txt_file(tmp_path, "a.txt", "A")
    file2 = create_txt_file(tmp_path, "b.txt", "BB")

    loader = DocumentLoader([file1, file2])
    docs = loader.load()

    assert len(docs) == 2

    contents = [doc["content"] for doc in docs]
    assert "A" in contents
    assert "BB" in contents


def test_docx_requires_dependency(tmp_path, monkeypatch):
    file_path = tmp_path / "test.docx"
    file_path.write_text("fake")

    loader = DocumentLoader([str(file_path)])

    # Force ImportError for docx
    def fake_import(*args, **kwargs):
        raise ImportError

    monkeypatch.setitem(__builtins__, "__import__", fake_import)

    with pytest.raises(ImportError):
        loader.load()


def test_empty_txt_file(tmp_path):
    file_path = create_txt_file(tmp_path, "empty.txt", "")

    loader = DocumentLoader([file_path])
    docs = loader.load()

    assert docs[0]["content"] == ""
    assert docs[0]["size"] == 0


def test_extension_case_insensitive(tmp_path):
    file_path = tmp_path / "file.TXT"
    file_path.write_text("Bonjour", encoding="utf-8")

    loader = DocumentLoader([str(file_path)])
    docs = loader.load()

    assert docs[0]["extension"] == ".txt"
