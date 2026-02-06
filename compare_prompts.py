"""
Advanced example: Compare prompt versions side-by-side
Demonstrates iterative prompt improvement
"""

import os
from rag_system import DocumentProcessor, RAGPipeline


def compare_prompts(pdf_path: str):
    """Compare V1 vs V2 prompts on the same questions"""
    
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return
    
    # Load documents
    processor = DocumentProcessor(chunk_size=500, overlap=100)
    text = processor.load_pdf(pdf_path)
    chunks = processor.chunk_text(text)
    
    # Initialize RAG
    rag = RAGPipeline()
    rag.add_documents(chunks)
    
    # Test questions
    test_questions = [
        "What is the refund policy?",
        "How long does shipping take?",
        "Can I return a damaged product?",
        "What are the office hours?"  # Likely unanswerable
    ]
    
    print("="*80)
    print("PROMPT COMPARISON: V1 vs V2")
    print("="*80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print(f"{'='*80}")
        
        # Get answers from both versions
        response_v1 = rag.answer_question(question, prompt_version=1)
        response_v2 = rag.answer_question(question, prompt_version=2)
        
        # Compare
        print("\n📝 PROMPT V1 (Basic):")
        print("-" * 80)
        print(response_v1['answer'])
        
        print("\n📝 PROMPT V2 (Improved):")
        print("-" * 80)
        print(response_v2['answer'])
        
        # Analysis
        print("\n📊 Analysis:")
        print("-" * 80)
        
        v1_has_citations = "Page" in response_v1['answer']
        v2_has_citations = "Page" in response_v2['answer'] or "Excerpt" in response_v2['answer']
        
        v1_has_confidence = "confidence" in response_v1['answer'].lower()
        v2_has_confidence = "Confidence:" in response_v2['answer']
        
        v1_structured = "**" in response_v1['answer']
        v2_structured = "**" in response_v2['answer']
        
        print(f"Citations:        V1: {'✓' if v1_has_citations else '✗'}  |  V2: {'✓' if v2_has_citations else '✗'}")
        print(f"Confidence:       V1: {'✓' if v1_has_confidence else '✗'}  |  V2: {'✓' if v2_has_confidence else '✗'}")
        print(f"Structured:       V1: {'✓' if v1_structured else '✗'}  |  V2: {'✓' if v2_structured else '✗'}")
        print(f"Retrieval Conf:   V1: {response_v1['confidence']}  |  V2: {response_v2['confidence']}")
        
        input("\nPress Enter to continue to next question...")
    
    print("\n" + "="*80)
    print("KEY DIFFERENCES:")
    print("="*80)
    print("""
V1 Prompt Characteristics:
- Simple, direct instructions
- No enforced structure
- Optional citations
- No confidence assessment
- May hallucinate when uncertain

V2 Prompt Improvements:
- XML tags for clear sections
- Structured output format enforced
- Required citations with page numbers
- Explicit confidence levels with criteria
- "Note" section for caveats
- Multi-step reasoning process

Result: V2 produces more grounded, reliable answers with better user trust.
    """)


if __name__ == "__main__":
    pdf_path = "policy_document.pdf"
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Please set ANTHROPIC_API_KEY environment variable")
    else:
        compare_prompts(pdf_path)
