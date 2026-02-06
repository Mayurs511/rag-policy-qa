from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

import os
from rag_system import DocumentProcessor, RAGPipeline, Evaluator


def main():
    """Run the RAG system demo"""
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  GROQ_API_KEY not set. Please set it to run the demo.")
        print("   For PowerShell: $env:GROQ_API_KEY='your-key-here'")
        print("   For Bash: export GROQ_API_KEY='your-key-here'")
        return
    
    # Check for PDF file
    pdf_path = "policy_document.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  Policy document not found: {pdf_path}")
        print("   Please place your doTERRA policy PDF in the current directory")
        print("   and name it 'policy_document.pdf'")
        return
    
    print("="*80)
    print("RAG SYSTEM FOR POLICY DOCUMENT Q&A")
    print("Using Groq API (llama-3.1-8b-instant)")
    print("="*80)
    
    # Step 1: Process documents
    print("\n📄 Step 1: Loading and processing documents...")
    processor = DocumentProcessor(chunk_size=500, overlap=100)
    
    # Load PDF
    text = processor.load_pdf(pdf_path)
    print(f"   Loaded {len(text)} characters from PDF")
    
    # Chunk text
    documents = processor.chunk_text(text, source=pdf_path)
    print(f"   Created {len(documents)} chunks")
    print(f"   Chunk size: {processor.chunk_size} chars with {processor.overlap} overlap")
    
    # Step 2: Initialize RAG pipeline
    print("\n🔧 Step 2: Initializing RAG pipeline...")
    rag = RAGPipeline(model_name="all-MiniLM-L6-v2")
    rag.add_documents(documents)
    
    # Step 3: Run evaluation
    print("\n📊 Step 3: Running evaluation...")
    evaluator = Evaluator()
    
    # Evaluation questions (mix of answerable, partial, and unanswerable)
    evaluation_questions = [
        {
            "query": "What is the refund policy for products?",
            "expected": "Should mention timeframe, conditions, and process for refunds",
            "category": "answerable"
        },
        {
            "query": "What happens if a Wellness Advocate violates the intellectual property usage rules?",
            "expected": "Should mention termination of rights, injunctive relief, and other remedies available to the company",
            "category": "answerable"
        },
        {
            "query": "Are Wellness Advocates allowed to sell dōTERRA products on Amazon or Flipkart?",
            "expected": "Should state that online marketplace sales are prohibited without written company authorization",
            "category": "answerable"
        },
        {
            "query": "Does dōTERRA provide legal protection if a customer claims injury from a product?",
            "expected": "Should explain company defense obligations and the exceptions to indemnification",
            "category": "answerable"
        },
        {
            "query": "Does the policy specify which social media platforms are allowed for promotion?",
            "expected": "Should mention some platforms explicitly but note that not all platforms are exhaustively listed",
            "category": "partially_answerable"
        },
        {
            "query": "What is the company's policy on damaged products?",
            "expected": "Should explain how to handle damaged items",
            "category": "answerable"
        },
        {
            "query": "How do I become a wholesale member?",
            "expected": "May not be in standard policy docs",
            "category": "potentially_unanswerable"
        },
        {
            "query": "What is the weather like in the company headquarters?",
            "expected": "Completely outside scope of policy documents",
            "category": "unanswerable"
        }
    ]
    
    print(f"\n   Evaluating {len(evaluation_questions)} questions...")
    print("   " + "-"*76)
    
    # Test with V2 prompt (improved version)
    print(f"\n   🔍 Testing with Improved Prompt (V2)")
    print("   " + "-"*76)
    
    for i, qa in enumerate(evaluation_questions, 1):
        query = qa["query"]
        
        print(f"\n   Q{i}: {query}")
        print(f"   Category: {qa['category']}")
        
        # Get answer
        response = rag.answer_question(query, top_k=3, prompt_version=2)
        
        print(f"   Confidence: {response['confidence']}")
        
        # Show answer (truncated)
        answer_preview = response['answer'][:150] + "..." if len(response['answer']) > 150 else response['answer']
        print(f"   Answer: {answer_preview}")
        
        # Evaluate
        eval_result = evaluator.evaluate_answer(
            query, 
            response, 
            expected_info=qa["expected"]
        )
    
    # Print summary
    evaluator.print_summary()
    
    # Save results
    evaluator.save_results("evaluation_results.json")
    print("\n✅ Evaluation results saved to: evaluation_results.json")
    
    # Step 4: Interactive mode
    print("\n" + "="*80)
    print("🤖 INTERACTIVE MODE")
    print("="*80)
    print("Ask questions about the policy (type 'quit' to exit)")
    print()
    
    # Interactive loop
    while True:
        try:
            # Get user input
            query = input("❓ Your question: ").strip()
            
            # Check for exit commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for using the RAG system!")
                break
            
            # Skip empty inputs (just pressing Enter)
            if not query:
                print("   (Please enter a question or type 'quit' to exit)\n")
                continue
            
            # Get answer using v2 prompt (improved)
            print("\n🔍 Searching policy documents...")
            response = rag.answer_question(query, top_k=3, prompt_version=2)
            
            print("\n💡 Answer:")
            print("-" * 80)
            print(response['answer'])
            print("-" * 80)
            
            print(f"\n📚 Retrieved {len(response['context'])} relevant excerpts:")
            for i, ctx in enumerate(response['context'], 1):
                print(f"   {i}. Page {ctx['page']} (relevance: {ctx['relevance_score']:.3f})")
            
            print()  # Empty line for readability
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Thank you for using the RAG system!")
            break
        except EOFError:
            print("\n\n👋 Thank you for using the RAG system!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()