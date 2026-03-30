from src.core import DocumentLoader
from src.core import TextProcessor

if __name__ == "__main__":
    # Create a loader with a list of files (replace with actual paths)
    loader = DocumentLoader(["example1.txt", "example2.txt"])
    docs = loader.load()

    for doc in docs:
        print(f"File: {doc['file_path']}")
        print(f"Length: {doc['size']} characters")
        print(f"First 200 characters:\n{doc['content'][:200]}\n")

processor = TextProcessor(language='french')

sample_text = docs[1]["content"]

# 1. Get sentences with metadata
sentences_metadata = processor.get_sentences_with_metadata(sample_text)

print("=== Sentences with Metadata ===")
for sent in sentences_metadata:
    print(f"Sentence {sent['id']}: {sent['text']}")
    print(f"  Words: {sent['words']}")
    print(f"  Lemmas: {sent['tagged_lemmas']}")
    print(f"  Word count: {sent['word_count']}\n")
