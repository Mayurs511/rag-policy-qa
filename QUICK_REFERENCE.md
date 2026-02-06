# Quick Reference Guide

## Installation (30 seconds)

```bash
# Automated setup
./setup.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-key-here'
```

---

## Running the System

### Full Demo
```bash
python demo.py
```
Runs evaluation + interactive Q&A

### Compare Prompts
```bash
python compare_prompts.py
```
Side-by-side comparison of V1 vs V2

### Quick Test
```python
from rag_system import DocumentProcessor, RAGPipeline

# Setup
processor = DocumentProcessor()
text = processor.load_pdf("policy_document.pdf")
chunks = processor.chunk_text(text)

rag = RAGPipeline()
rag.add_documents(chunks)

# Ask
response = rag.answer_question("What is the refund policy?")
print(response['answer'])
```

---

## File Structure

```
rag-policy-qa/
├── rag_system.py          # Core RAG implementation ⭐
├── demo.py                # Full demo script
├── compare_prompts.py     # Prompt comparison
├── langchain_bonus.py     # LangChain integration
├── setup.sh               # Automated setup
├── requirements.txt       # Dependencies
├── README.md              # Main documentation ⭐
├── EVALUATION.md          # Evaluation methodology
├── SUBMISSION_NOTES.md    # For interviewer ⭐
└── .gitignore             # Git ignore rules
```

**Start here**: README.md  
**Key code**: rag_system.py  
**For interviewer**: SUBMISSION_NOTES.md

---

## API

### DocumentProcessor
```python
processor = DocumentProcessor(chunk_size=500, overlap=100)
text = processor.load_pdf("path/to/file.pdf")
chunks = processor.chunk_text(text, source="file.pdf")
```

### RAGPipeline
```python
rag = RAGPipeline(model_name="all-MiniLM-L6-v2")
rag.add_documents(chunks)

# Ask question with V2 prompt
response = rag.answer_question(
    query="Your question?",
    top_k=3,
    prompt_version=2
)

# Response structure
{
    "query": "...",
    "answer": "...",
    "context": [...],
    "confidence": "high|medium|low",
    "retrieval_scores": [...]
}
```

### Evaluator
```python
evaluator = Evaluator()
result = evaluator.evaluate_answer(query, response, expected_info)
evaluator.print_summary()
evaluator.save_results("results.json")
```

---

## Prompt Versions

### V1 (Basic)
- Simple instructions
- No enforced structure
- Optional citations

### V2 (Improved) ✅
- XML tags for sections
- Required citations
- Confidence levels
- Structured output
- "Note" section for caveats

**Use V2 for production**

---

## Common Issues

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

### "No module named 'faiss'"
```bash
pip install faiss-cpu
```

### "policy_document.pdf not found"
- Add PDF to project root
- Name it exactly: `policy_document.pdf`

### Embeddings download slow
First run downloads 90MB model. Wait ~2 minutes.

---

## Customization

### Change chunk size
```python
processor = DocumentProcessor(
    chunk_size=1000,  # Larger chunks
    overlap=200       # More overlap
)
```

### Change retrieval count
```python
response = rag.answer_question(query, top_k=5)  # Get 5 chunks
```

### Use different embedding model
```python
rag = RAGPipeline(model_name="all-mpnet-base-v2")  # Larger, better
```

### Change LLM model
Edit `rag_system.py`:
```python
message = self.anthropic_client.messages.create(
    model="claude-opus-4-20250514",  # Use Opus instead
    ...
)
```

---

## Performance Tips

### Speed up retrieval
```python
# Use GPU FAISS (if available)
import faiss
index = faiss.IndexFlatL2(dimension)
if faiss.get_num_gpus() > 0:
    index = faiss.index_cpu_to_gpu(
        faiss.StandardGpuResources(), 
        0, 
        index
    )
```

### Reduce costs
```python
# Use Haiku instead of Sonnet
model="claude-haiku-4-20250514"
```

### Better accuracy
```python
# Retrieve more, but only use top 3
rough_results = rag.retrieve(query, top_k=10)
# ... rerank ...
final_results = reranked[:3]
```

---

## Evaluation Checklist

Run before submitting:

- [ ] `python demo.py` runs successfully
- [ ] All 8 test questions execute
- [ ] V2 prompt includes citations
- [ ] Edge cases handled (unanswerable questions)
- [ ] evaluation_results.json created
- [ ] README.md is clear and complete

---

## Next Steps

1. **Add reranking** → 15-20% accuracy boost
2. **Implement caching** → Faster for repeated queries
3. **Add logging** → Better debugging
4. **User feedback loop** → Learn from mistakes
5. **A/B test prompts** → Continuous improvement

---

## Resources

- [Claude API Docs](https://docs.anthropic.com)
- [FAISS Docs](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net)
- [Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)

---

## Getting Help

1. Check README.md
2. Review EVALUATION.md
3. Read code comments in rag_system.py
4. Check GitHub issues (if applicable)

---

**Built with ❤️ for NeuraAI**
