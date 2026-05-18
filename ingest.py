import os
import hashlib
import json

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# הגדרת תיקיות
KB_DIR = "knowledge_base"
DB_DIR = os.path.join("data", "chroma")
HASH_FILE = os.path.join("data", "indexed_files.json")

def get_file_hash(filepath):
    """מחשב חתימה ייחודית לקובץ כדי לדעת אם הוא השתנה"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()

def load_indexed_hashes():
    """טוען את רשימת הקבצים שכבר אינדקסנו"""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_indexed_hashes(hashes):
    """שומר את רשימת הקבצים המעודכנת"""
    with open(HASH_FILE, 'w', encoding='utf-8') as f:
        json.dump(hashes, f, ensure_ascii=False, indent=4)

def main():
    # מוודא שהתיקייה קיימת
    os.makedirs(KB_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    files_to_process = [f for f in os.listdir(KB_DIR) if f.endswith(('.pdf', '.txt'))]
    
    if not files_to_process:
        print(f"📂 התיקייה '{KB_DIR}' ריקה. שים שם קבצי PDF או TXT והרץ מחדש.")
        return

    indexed_hashes = load_indexed_hashes()
    new_documents = []
    updated_hashes = indexed_hashes.copy()

    print("🔍 סורק קבצים...")
    for filename in files_to_process:
        filepath = os.path.join(KB_DIR, filename)
        file_hash = get_file_hash(filepath)

        # בדיקת Re-indexing
        if filename in indexed_hashes and indexed_hashes[filename] == file_hash:
            print(f"⏭️ מדלג על {filename} (כבר מאונדקס ולא השתנה)")
            continue

        print(f"📄 קורא את {filename}...")
        if filename.endswith('.pdf'):
            loader = PyPDFLoader(filepath)
        else:
            loader = TextLoader(filepath, encoding='utf-8')
            
        docs = loader.load()
        new_documents.extend(docs)
        updated_hashes[filename] = file_hash

    if not new_documents:
        print("✅ אין קבצים חדשים לאנדקס. הכל מעודכן!")
        return

    print("✂️ חותך את הטקסט לפסקאות (Chunking)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(new_documents)
    print(f"✅ נוצרו {len(chunks)} מקטעי טקסט.")

    print("🧠 טוען את מודל ה-Embeddings לעברית (intfloat/multilingual-e5-small)...")
    # זה עלול לקחת כמה שניות בפעם הראשונה כי הוא מוריד את המודל למחשב
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-small",
        model_kwargs={'local_files_only': True}
    )

    print("💾 שומר את הווקטורים במסד הנתונים (ChromaDB)...")
    # יצירת החיבור למסד הנתונים המקומי ושמירת המקטעים
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
        collection_name="deep_agent_knowledge"
    )

    # עדכון קובץ המעקב
    save_indexed_hashes(updated_hashes)
    print("🎉 האינדוקס הסתיים בהצלחה!")

if __name__ == "__main__":
    main()