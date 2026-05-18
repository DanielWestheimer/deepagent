import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DB_DIR = os.path.join("data", "chroma")

class RAGEngine:
    def __init__(self):
        # טוען את המודל (בפעם השנייה זה נטען מהזיכרון המקומי תוך שנייה)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-small",
            model_kwargs={'local_files_only': True}
        )
        
        # מתחבר למסד הנתונים הקיים
        self.db = Chroma(
            persist_directory=DB_DIR,
            embedding_function=self.embeddings,
            collection_name="deep_agent_knowledge"
        )

    def search(self, query: str, k: int = 3) -> str:
        """
        מקבל שאילתת חיפוש, מחפש ב-ChromaDB,
        ומחזיר מחרוזת מעוצבת עם k התוצאות הכי רלוונטיות.
        """
        # ביצוע החיפוש הווקטורי
        results = self.db.similarity_search(query, k=k)
        
        if not results:
            return "לא נמצאו תוצאות רלוונטיות במסד הנתונים."
            
        # עיצוב התוצאות לטקסט קריא שהסוכן (קלוד) יוכל להבין בקלות
        formatted_results = []
        for i, doc in enumerate(results):
            # חילוץ שם הקובץ מהנתיב המלא
            source_path = doc.metadata.get("source", "Unknown")
            source_file = os.path.basename(source_path)
            
            formatted_results.append(
                f"--- תוצאה {i+1} (מקור: {source_file}) ---\n{doc.page_content}"
            )
            
        return "\n\n".join(formatted_results)

# בלוק בדיקה: ירוץ רק אם נפעיל את הקובץ ישירות
if __name__ == "__main__":
    print("🚀 מאתחל את מנוע החיפוש...")
    engine = RAGEngine()
    
    print("\n✅ המנוע מוכן!")
    while True:
        user_query = input("\nהכנס מילות חיפוש (או 'q' ליציאה): ")
        if user_query.lower() == 'q':
            break
            
        print("\nמחפש...")
        answer = engine.search(user_query)
        print("\n" + "="*40)
        print(answer)
        print("="*40)