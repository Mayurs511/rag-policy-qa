"""
RAG System for Policy Document Question Answering
Built for NeuraAI AI Engineer Intern Assignment
Using Groq API (llama-3.1-8b-instant)
"""

import os
import json
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

# For PDF processing
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")

# For embeddings and vector storage
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("sentence-transformers not installed. Install with: pip install sentence-transformers")

try:
    import faiss
except ImportError:
    print("faiss not installed. Install with: pip install faiss-cpu")

# For LLM - Groq only
try:
    from groq import Groq
except ImportError:
    print("groq not installed. Install with: pip install groq")


@dataclass
class Document:
    """Represents a text chunk with metadata"""
    text: str
    chunk_id: int
    page_num: int
    source: str


class DocumentProcessor:
    """Handles PDF loading and text chunking"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        Initialize document processor
        
        Args:
            chunk_size: Number of characters per chunk (default: 500)
            overlap: Number of characters to overlap between chunks (default: 100)
        
        Rationale for chunk_size=500:
        - Policy documents contain discrete sections (refund rules, shipping info, etc.)
        - 500 chars (~100-125 tokens) captures complete policy statements
        - Small enough for focused retrieval, large enough for context
        - Overlap of 100 chars prevents splitting mid-sentence/policy
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def load_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n[Page {page_num + 1}]\n{page_text}"
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\[\]]', '', text)
        return text.strip()
    
    def chunk_text(self, text: str, source: str = "policy.pdf") -> List[Document]:
        """
        Split text into overlapping chunks
        
        Uses sliding window approach to maintain context continuity
        """
        chunks = []
        chunk_id = 0
        
        # Extract page numbers if available
        page_pattern = r'\[Page (\d+)\]'
        sections = re.split(page_pattern, text)
        
        current_page = 1
        for i in range(1, len(sections), 2):
            if i < len(sections):
                current_page = int(sections[i])
                page_text = sections[i + 1] if i + 1 < len(sections) else ""
                
                # Clean the page text
                page_text = self.clean_text(page_text)
                
                # Create chunks from this page
                start = 0
                while start < len(page_text):
                    end = start + self.chunk_size
                    chunk_text = page_text[start:end]
                    
                    # Don't create tiny chunks at the end
                    if len(chunk_text) < 50 and chunks:
                        chunks[-1].text += " " + chunk_text
                    else:
                        chunks.append(Document(
                            text=chunk_text,
                            chunk_id=chunk_id,
                            page_num=current_page,
                            source=source
                        ))
                        chunk_id += 1
                    
                    start += self.chunk_size - self.overlap
        
        return chunks


class RAGPipeline:
    """Main RAG system with embedding, retrieval, and generation using Groq"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG pipeline
        
        Args:
            model_name: SentenceTransformer model for embeddings
                       (all-MiniLM-L6-v2: fast, good quality, 384 dims)
        """
        self.embedding_model = SentenceTransformer(model_name)
        self.documents: List[Document] = []
        self.index = None
        self.groq_client = None
        
        # Initialize Groq client
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)
            print("✓ Groq API client initialized successfully")
        else:
            print("⚠️ GROQ_API_KEY not set. Please set it to use the LLM.")
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the knowledge base"""
        self.documents = documents
        
        # Generate embeddings
        texts = [doc.text for doc in documents]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"✓ Added {len(documents)} documents to the index")
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """
        Retrieve most relevant documents for a query
        
        Args:
            query: User question
            top_k: Number of documents to retrieve
        
        Returns:
            List of (Document, similarity_score) tuples
        """
        # Embed query
        query_embedding = self.embedding_model.encode([query])
        
        # Search
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Return documents with scores
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(distance)))
        
        return results
    
    def generate_answer_v1(self, query: str, context_docs: List[Document]) -> str:
        """
        Version 1: Initial prompt (basic, direct)
        
        Prompt Design Principles:
        - Clear role definition
        - Explicit instruction to use only provided context
        - Fallback for missing information
        """
        if not self.groq_client:
            return "Error: GROQ_API_KEY not set. Cannot generate answer."
        
        # Prepare context
        context = "\n\n".join([
            f"[Excerpt {i+1} from Page {doc.page_num}]:\n{doc.text}"
            for i, doc in enumerate(context_docs)
        ])
        
        prompt = f"""You are a helpful assistant answering questions about company policies.

Context from policy documents:
{context}

Question: {query}

Instructions:
- Answer the question using ONLY the information provided in the context above
- If the context doesn't contain the answer, say "I don't have enough information to answer this question"
- Be concise and accurate

Answer:"""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def generate_answer_v2(self, query: str, context_docs: List[Document]) -> str:
        """
        Version 2: Improved prompt with structured output and better grounding
        
        Improvements over v1:
        1. Structured output format (Policy, Details, Source)
        2. Explicit citation requirement (page numbers)
        3. Stronger hallucination prevention with multi-step reasoning
        4. Graceful degradation for partial information
        5. XML tags for clear section separation
        """
        if not self.groq_client:
            return "Error: GROQ_API_KEY not set. Cannot generate answer."
        
        # Prepare context with clear labeling
        context = "\n\n".join([
            f"<excerpt id=\"{i+1}\" page=\"{doc.page_num}\">\n{doc.text}\n</excerpt>"
            for i, doc in enumerate(context_docs)
        ])
        
        prompt = f"""You are a precise policy assistant. Your task is to answer questions about company policies using ONLY the provided excerpts.

<policy_excerpts>
{context}
</policy_excerpts>

<question>
{query}
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
[Your answer here, with citations like (Excerpt 1, Page 5)]

**Confidence:** [High/Medium/Low]
- High: Answer fully supported by excerpts
- Medium: Partial information available
- Low: Insufficient information

**Source:** [List excerpt IDs and page numbers used]

**Note:** [Any important caveats or missing information]
</output_format>

Please answer the question now:"""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def answer_question(self, query: str, top_k: int = 3, prompt_version: int = 2) -> Dict:
        """
        End-to-end question answering
        
        Args:
            query: User question
            top_k: Number of documents to retrieve
            prompt_version: Which prompt to use (1 or 2)
        
        Returns:
            Dictionary with answer, context, and metadata
        """
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, top_k)
        
        # Check if we have relevant results (threshold: distance < 1.5)
        if not retrieved_docs or retrieved_docs[0][1] > 1.5:
            return {
                "query": query,
                "answer": "I couldn't find relevant information in the policy documents to answer this question. This topic may not be covered in the available policies.",
                "context": [],
                "confidence": "low",
                "retrieval_scores": []
            }
        
        # Extract documents
        docs = [doc for doc, _ in retrieved_docs]
        scores = [score for _, score in retrieved_docs]
        
        # Generate answer
        if prompt_version == 1:
            answer = self.generate_answer_v1(query, docs)
        else:
            answer = self.generate_answer_v2(query, docs)
        
        return {
            "query": query,
            "answer": answer,
            "context": [
                {
                    "text": doc.text,
                    "page": doc.page_num,
                    "chunk_id": doc.chunk_id,
                    "relevance_score": float(score)
                }
                for doc, score in zip(docs, scores)
            ],
            "confidence": self._assess_confidence(scores),
            "retrieval_scores": scores
        }
    
    def _assess_confidence(self, scores: List[float]) -> str:
        """Assess retrieval confidence based on similarity scores"""
        if not scores:
            return "low"
        
        best_score = scores[0]
        if best_score < 0.5:
            return "high"
        elif best_score < 1.0:
            return "medium"
        else:
            return "low"


class Evaluator:
    """Evaluate RAG system performance"""
    
    def __init__(self):
        self.results = []
    
    def evaluate_answer(self, query: str, response: Dict, expected_info: str = None) -> Dict:
        """
        Evaluate a single question-answer pair
        
        Args:
            query: The question asked
            response: RAG system response
            expected_info: What we expect in a good answer (for manual eval)
        
        Returns:
            Evaluation metrics
        """
        answer = response["answer"]
        
        # Check for hallucination indicators
        hallucination_red_flags = [
            "I don't have" in answer,
            "not found" in answer,
            "cannot answer" in answer,
            "insufficient information" in answer
        ]
        
        admits_limitation = any(hallucination_red_flags)
        
        # Scoring
        evaluation = {
            "query": query,
            "answer": answer,
            "retrieval_confidence": response["confidence"],
            "admits_limitation": admits_limitation,
            "has_citations": "Page" in answer or "Excerpt" in answer,
            "context_used": len(response["context"]),
            "expected_info": expected_info
        }
        
        # Manual scoring (to be filled in)
        evaluation["accuracy"] = None  # ✅ / ⚠️ / ❌
        evaluation["notes"] = ""
        
        self.results.append(evaluation)
        return evaluation
    
    def print_summary(self):
        """Print evaluation summary"""
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        
        for i, result in enumerate(self.results, 1):
            print(f"\n{i}. Query: {result['query']}")
            print(f"   Confidence: {result['retrieval_confidence']}")
            print(f"   Citations: {'✓' if result['has_citations'] else '✗'}")
            print(f"   Admits limitations: {'✓' if result['admits_limitation'] else '✗'}")
            print(f"   Context chunks: {result['context_used']}")
            if result['accuracy']:
                print(f"   Accuracy: {result['accuracy']}")
        
        print("\n" + "="*80)
    
    def save_results(self, filepath: str):
        """Save evaluation results to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)


if __name__ == "__main__":
    print("RAG System initialized. See demo.py for usage examples.")