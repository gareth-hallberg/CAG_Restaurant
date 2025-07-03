import os
from typing import List, Dict, Any
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, DirectoryReadTool
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import markdown
from bs4 import BeautifulSoup

load_dotenv()


class CAGSystem:
    def __init__(self, data_folder: str = "BellaTerra"):
        self.data_folder = data_folder
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = None
        self.setup_vectorstore()
        self.file_tool = FileReadTool()
        self.directory_tool = DirectoryReadTool(directory=data_folder)
        
    def setup_vectorstore(self):
        """Initialize the vector store with markdown documents"""
        # Use OpenAI embeddings
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="bella_terra_menus",
            embedding_function=openai_ef
        )
        
        # Check if already populated
        if self.collection.count() > 0:
            print(f"Vector store already populated with {self.collection.count()} documents")
            return
        
        # Load and process markdown files
        documents = []
        metadatas = []
        ids = []
        
        for i, filename in enumerate(os.listdir(self.data_folder)):
            if filename.endswith('.md'):
                file_path = os.path.join(self.data_folder, filename)
                
                # Read markdown file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Convert markdown to plain text
                html = markdown.markdown(content)
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
                
                # Split into chunks
                chunks = self._split_text(text, chunk_size=1000, overlap=200)
                
                for j, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "source": filename,
                        "chunk_index": j
                    })
                    ids.append(f"{filename}_{j}")
        
        # Add to collection
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
    
    def create_agents(self):
        """Create CrewAI agents for the CAG system"""
        
        # Context Analyst Agent
        self.context_analyst = Agent(
            role='Context Analyst',
            goal='Analyze and extract relevant context from the Bella Terra menu knowledge base',
            backstory="""You are an expert at understanding and analyzing restaurant 
            information, menus, and business data. You excel at finding relevant 
            information and understanding relationships between different pieces of data.
            You work with the Bella Terra restaurant's menu data.""",
            verbose=True,
            allow_delegation=False,
            tools=[self.file_tool, self.directory_tool]
        )
        
        # Context Augmenter Agent
        self.context_augmenter = Agent(
            role='Context Augmenter',
            goal='Enhance and expand context with additional insights about menu items and relationships',
            backstory="""You specialize in enriching context by identifying patterns, 
            relationships, and implicit information in restaurant menus. You can infer 
            additional context from existing data and make intelligent connections between
            dishes, ingredients, prices, and categories.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Response Generator Agent
        self.response_generator = Agent(
            role='Response Generator',
            goal='Generate comprehensive responses about Bella Terra using augmented context',
            backstory="""You are a master at crafting detailed, accurate, and helpful 
            responses about restaurant menus and offerings. You use all available context 
            to provide the most relevant and complete answers possible about Bella Terra.""",
            verbose=True,
            allow_delegation=False
        )
    
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
    
    def augment_context(self, query: str, initial_context: List[Dict[str, Any]]) -> str:
        """Use agents to augment the retrieved context"""
        
        # Format context for agents
        context_str = "\n\n".join([
            f"From {ctx['source']}:\n{ctx['content']}" 
            for ctx in initial_context
        ])
        
        # Task 1: Analyze initial context
        context_analysis_task = Task(
            description=f"""Analyze the following context pieces from Bella Terra's menus for the query: '{query}'
            
            Context pieces:
            {context_str}
            
            Identify key information, relationships between menu items, price patterns, 
            and any gaps in the context. Focus on understanding the restaurant's offerings.""",
            expected_output="A detailed analysis of the menu context with key insights about dishes, prices, and categories",
            agent=self.context_analyst
        )
        
        # Task 2: Augment context
        augmentation_task = Task(
            description="""Based on the context analysis, augment the information by:
            1. Identifying implicit relationships between menu items, prices, and categories
            2. Inferring additional relevant details about ingredients or preparation methods
            3. Suggesting related menu items or pairings that might be helpful
            4. Highlighting any special patterns, pricing tiers, or menu groupings
            5. Making connections between different menu sections (pizza, pasta, wine, etc.)""",
            expected_output="Enhanced context with additional insights about Bella Terra's offerings",
            agent=self.context_augmenter,
            context=[context_analysis_task]
        )
        
        # Task 3: Generate response
        generation_task = Task(
            description=f"""Using all the analyzed and augmented context about Bella Terra, 
            generate a comprehensive response to the query: '{query}'
            
            Ensure the response is:
            - Accurate to the source menu data
            - Enhanced with the augmented insights about relationships and patterns
            - Well-structured and easy to understand
            - Complete with all relevant details including prices where applicable
            - Helpful for someone trying to understand Bella Terra's offerings""",
            expected_output="A comprehensive, friendly response about Bella Terra's menu offerings",
            agent=self.response_generator,
            context=[context_analysis_task, augmentation_task]
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[self.context_analyst, self.context_augmenter, self.response_generator],
            tasks=[context_analysis_task, augmentation_task, generation_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Main method to process a query through the CAG system"""
        print(f"\n🔍 Processing query: {query}")
        
        # Retrieve initial context
        initial_context = self.retrieve_context(query)
        print(f"\n📚 Retrieved {len(initial_context)} context chunks")
        
        # Create agents if not already created
        if not hasattr(self, 'context_analyst'):
            self.create_agents()
        
        # Augment context and generate response
        augmented_response = self.augment_context(query, initial_context)
        
        return {
            "query": query,
            "initial_context": initial_context,
            "augmented_response": augmented_response
        }


def main():
    # Example usage
    cag = CAGSystem()
    
    # Example queries
    queries = [
        "What pizza options are available and what makes them special?",
        "Can you recommend a wine pairing for pasta?",
        "What are the lunch specials at Bella Terra?"
    ]
    
    for query in queries[:1]:  # Just run one example
        result = cag.process_query(query)
        print("\n" + "="*80)
        print(f"Query: {query}")
        print(f"Response: {result['augmented_response']}")
        print("="*80 + "\n")


if __name__ == "__main__":
    main()