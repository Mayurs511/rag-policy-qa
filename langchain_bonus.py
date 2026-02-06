"""
BONUS: LangChain Integration Example
Shows how to extend the RAG system with LangChain for more advanced workflows
"""

# Uncomment to use (requires: pip install langchain langchain-anthropic)

"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_anthropic import ChatAnthropic
from langchain.schema import Document as LangChainDocument
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

class LangChainRAG:
    '''
    Enhanced RAG using LangChain for:
    - Prompt templating
    - Chain orchestration  
    - Better observability
    '''
    
    def __init__(self):
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize LLM
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0
        )
        
        # Vector store (will be populated)
        self.vectorstore = None
        
    def add_documents(self, documents):
        '''Add documents to vector store'''
        # Convert to LangChain format
        langchain_docs = [
            LangChainDocument(
                page_content=doc.text,
                metadata={
                    "page": doc.page_num,
                    "chunk_id": doc.chunk_id,
                    "source": doc.source
                }
            )
            for doc in documents
        ]
        
        # Create FAISS index
        self.vectorstore = FAISS.from_documents(
            langchain_docs, 
            self.embeddings
        )
    
    def create_qa_chain(self):
        '''Create a question-answering chain'''
        
        # Define prompt template (V2 style)
        template = '''You are a precise policy assistant. Answer questions using ONLY the provided excerpts.

<policy_excerpts>
{context}
</policy_excerpts>

<question>
{question}
</question>

<instructions>
1. CAREFULLY read all excerpts
2. ONLY use information explicitly stated in the excerpts
3. If the answer requires information not in the excerpts, state this clearly
4. Cite the excerpt ID and page number for each piece of information
5. Use the structured format below
</instructions>

<output_format>
**Policy Answer:**
[Your answer here, with citations like (Page X)]

**Confidence:** [High/Medium/Low]
- High: Answer fully supported by excerpts
- Medium: Partial information available
- Low: Insufficient information

**Source:** [List page numbers used]

**Note:** [Any important caveats or missing information]
</output_format>

Please answer the question now:'''
        
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )
        
        # Create chain
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt
        )
        
        return chain
    
    def answer_question(self, query: str, k: int = 3):
        '''Answer a question using the RAG chain'''
        
        # Retrieve relevant documents
        docs = self.vectorstore.similarity_search(query, k=k)
        
        # Format context
        context = "\\n\\n".join([
            f"<excerpt page=\\"{doc.metadata['page']}\\">\\n{doc.page_content}\\n</excerpt>"
            for doc in docs
        ])
        
        # Run chain
        chain = self.create_qa_chain()
        response = chain.run(context=context, question=query)
        
        return {
            "answer": response,
            "source_docs": docs
        }


# Example usage
if __name__ == "__main__":
    '''
    # Load your documents
    from rag_system import DocumentProcessor
    
    processor = DocumentProcessor()
    text = processor.load_pdf("policy_document.pdf")
    chunks = processor.chunk_text(text)
    
    # Initialize LangChain RAG
    langchain_rag = LangChainRAG()
    langchain_rag.add_documents(chunks)
    
    # Ask questions
    response = langchain_rag.answer_question("What is the refund policy?")
    print(response["answer"])
    '''
    
    print("LangChain integration example (commented out)")
    print("Uncomment code in this file and install: pip install langchain langchain-anthropic")
'''

# Benefits of LangChain Integration:
# 
# 1. PROMPT MANAGEMENT
#    - Centralized prompt templates
#    - Easy A/B testing of prompts
#    - Version control for prompts
# 
# 2. CHAIN ORCHESTRATION  
#    - Multi-step reasoning
#    - Conditional logic
#    - Error handling
# 
# 3. OBSERVABILITY
#    - Built-in logging
#    - Token counting
#    - Performance tracking
# 
# 4. EXTENSIBILITY
#    - Easy to add agents
#    - Tool integration
#    - Memory management
# 
# Trade-offs:
# - More complex (steeper learning curve)
# - Additional dependencies
# - Slight performance overhead
# 
# When to use:
# - Production systems with complex workflows
# - Need for prompt versioning
# - Multi-agent systems
# - Advanced observability requirements
