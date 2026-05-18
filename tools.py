import subprocess
import os
import pdfplumber
from langchain_core.tools import tool
import hashlib
import json
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag import RAGEngine
rag_engine = None

def get_rag_engine():
    """פונקציה שדואגת לטעון את המודל רק בפעם הראשונה שצריך אותו"""
    global rag_engine
    if rag_engine is None:
        print("🧠 טוען את מודל ה-RAG לזיכרון (טעינה ראשונית)...")
        rag_engine = RAGEngine()
    return rag_engine

@tool
def execute_shell_command(command: str) -> str:
    """
    Use this tool to execute general shell/terminal commands. 
    Avoid using this for reading files or listing directories with Hebrew names.
    """
    try:
        print(f"\n[Tool Execution] Running Shell: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully."
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Execution failed: {str(e)}"

@tool
def list_files_in_directory(folder_path: str) -> str:
    """
    Use this tool to list all files in a specific folder. 
    It is very reliable for folders with Hebrew names and spaces.
    """
    try:
        print(f"\n[Tool Execution] Listing Directory: {folder_path}")
        # פייתון מטפל בעברית בנתיבים בצורה מושלמת לעומת ה-CMD
        files = os.listdir(folder_path)
        if not files:
            return "The directory is empty."
        
        return "\n".join([f"- {f}" for f in files])
    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def read_pdf_content(file_path: str) -> str:
    """
    Use this tool to read the text content of a PDF file. 
    Safe for Hebrew file names and handles text extraction directly.
    """
    try:
        print(f"\n[Tool Execution] Reading PDF: {file_path}")
        all_text = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text.append(f"--- Page {i+1} ---\n{text}")
        
        if not all_text:
            return "PDF opened but no text found (it might be scanned/images)."
            
        return "\n\n".join(all_text)
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

@tool
def search_knowledge_base(query: str) -> str:
    """
    חיפוש בבסיס הידע המקומי של המשתמש (RAG).
    השתמש בכלי זה בכל פעם שאתה נשאל על מידע ספציפי, נתונים, או מסמכים של המשתמש שלא נתנו לך במפורש.
    הכנס שאילתת חיפוש ממוקדת (עדיף בעברית).
    """
    print(f"\n🛠️ [Tool Execution] מחפש בבסיס הידע: '{query}'")
    try:
        engine = get_rag_engine()
        return engine.search(query)
    except Exception as e:
        return f"אירעה שגיאה בחיפוש: {str(e)}"

HASH_FILE = os.path.join("data", "indexed_files.json")

def get_file_hash(filepath):
    """מחשב חתימה ייחודית לקובץ כדי לדעת אם הוא השתנה"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()

@tool
def index_directory(folder_path: str) -> str:
    """
    סורק ולומד תיקייה המכילה קבצי PDF או TXT כדי שהמידע בהם יהיה זמין לחיפוש עתידי בבסיס הידע (RAG).
    הפעל כלי זה כאשר המשתמש מבקש ממך ללמוד, לקרוא או לאנדקס תיקייה חדשה.
    הכנס את הנתיב המלא של התיקייה.
    """
    if not os.path.isdir(folder_path):
        return f"שגיאה: התיקייה '{folder_path}' לא קיימת או שהנתיב שגוי."

    print(f"\n🛠️ [Tool Execution] מאנדקס תיקייה: {folder_path}")

    # טעינת קובץ המעקב
    indexed_hashes = {}
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r', encoding='utf-8') as f:
            try:
                indexed_hashes = json.load(f)
            except Exception:
                pass

    files_to_process = [f for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.txt'))]
    if not files_to_process:
        return f"לא נמצאו קבצי PDF או TXT בתיקייה '{folder_path}'."

    new_documents = []
    updated_hashes = indexed_hashes.copy()
    skipped_count = 0

    for filename in files_to_process:
        filepath = os.path.join(folder_path, filename)
        file_hash = get_file_hash(filepath)
        
        # שימוש בנתיב המוחלט כדי למנוע התנגשויות בין קבצים עם שם זהה בתיקיות שונות
        abs_path = os.path.abspath(filepath)

        # דילוג על קבצים שלא השתנו
        if abs_path in indexed_hashes and indexed_hashes[abs_path] == file_hash:
            skipped_count += 1
            continue

        try:
            print(f"📄 קורא את {filename}...")
            if filename.lower().endswith('.pdf'):
                loader = PyPDFLoader(filepath)
            else:
                loader = TextLoader(filepath, encoding='utf-8')
            
            docs = loader.load()
            # מעדכנים את המטא-דאטה שיידע מאיזה נתיב מדויק הקובץ הגיע
            for doc in docs:
                doc.metadata["source"] = abs_path
            
            new_documents.extend(docs)
            updated_hashes[abs_path] = file_hash
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")

    if not new_documents:
        return f"כל {len(files_to_process)} הקבצים בתיקייה כבר מאונדקסים המידע בהם מעודכן."

    print("✂️ חותך את הטקסט ומכניס למסד הנתונים הווקטורי...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(new_documents)

    try:
        # הקסם: שימוש במנוע הקיים שכבר טעון בזיכרון כדי להוסיף את המסמכים!
        engine = get_rag_engine()
        engine.db.add_documents(chunks)        
        # שמירת קובץ החתימות המעודכן
        with open(HASH_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_hashes, f, ensure_ascii=False, indent=4)
            
        return f"✅ אינדוקס הושלם בהצלחה! למדתי {len(new_documents)} קבצים חדשים/מעודכנים. דילגתי על {skipped_count} קבצים שכבר הכרתי."
    
    except Exception as e:
        return f"שגיאה במהלך שמירת הנתונים למסד: {str(e)}"

agent_tools = [execute_shell_command, list_files_in_directory, read_pdf_content, search_knowledge_base, index_directory]