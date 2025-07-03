import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import markdown
from bs4 import BeautifulSoup

load_dotenv()


class CAGSystemFast:
    """Simplified CAG system for faster responses during development"""
    
    def __init__(self, data_folder: str = "BellaTerra"):
        self.data_folder = data_folder
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = None
        self.setup_vectorstore()
        
    def setup_vectorstore(self):
        """Initialize the vector store with markdown documents"""
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="bella_terra_menus",
            embedding_function=openai_ef
        )
        
        if self.collection.count() > 0:
            print(f"Vector store already populated with {self.collection.count()} documents")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for i, filename in enumerate(os.listdir(self.data_folder)):
            if filename.endswith('.md'):
                file_path = os.path.join(self.data_folder, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                html = markdown.markdown(content)
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
                
                chunks = self._split_text(text, chunk_size=1000, overlap=200)
                
                for j, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "source": filename,
                        "chunk_index": j
                    })
                    ids.append(f"{filename}_{j}")
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Added {len(documents)} chunks to vector store")
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text splitter"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def retrieve_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context from the vector store"""
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        contexts = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                contexts.append({
                    'content': doc,
                    'source': results['metadatas'][0][i]['source'] if results['metadatas'] else 'Unknown'
                })
        
        return contexts
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query using simple OpenAI completion instead of agents"""
        import openai
        
        print(f"\n🔍 Processing query (fast mode): {query}")
        
        # Retrieve initial context
        initial_context = self.retrieve_context(query)
        print(f"\n📚 Retrieved {len(initial_context)} context chunks")
        
        # Format context
        context_str = "\n\n".join([
            f"From {ctx['source']}:\n{ctx['content']}" 
            for ctx in initial_context
        ])
        
        # Use OpenAI directly for faster response
        client = openai.OpenAI()
        
        prompt = f"""You are an AI assistant for Bella Terra restaurant. Using the following context from the restaurant's menus, answer the customer's question.

Context:
{context_str}

Customer Question: {query}

Provide a helpful, accurate response based on the menu information. If prices are mentioned, include them. Be friendly and informative."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful restaurant assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            "query": query,
            "initial_context": initial_context,
            "augmented_response": response.choices[0].message.content
        }


# Update the API to use fast mode optionally
if __name__ == "__main__":
    # Test the fast system
    cag = CAGSystemFast()
    result = cag.process_query("What beers are available for less than £6?")
    print(f"\nResponse: {result['augmented_response']}")