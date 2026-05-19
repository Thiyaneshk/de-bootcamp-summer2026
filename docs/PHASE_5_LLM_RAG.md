# Phase 5: LLM + RAG Integration (Optional)

## Overview

Phase 5 teaches you how to:
- Set up local LLM with Ollama
- Implement RAG (Retrieval-Augmented Generation)
- Query financial data using natural language
- Build a chat interface for data analysis

**Time to Complete:** 2-3 hours  
**Tech Stack:** Ollama, LangChain, Streamlit, Vector databases

**Prerequisites:** Complete Phase 4 (Analytics dashboards working)

**Note:** This phase is optional but demonstrates modern AI/ML integration with data engineering.

---

## Learning Goals

- ✅ Understand LLM concepts and limitations
- ✅ Set up local LLM (Ollama) vs cloud APIs
- ✅ Implement RAG pattern for grounding LLM with data
- ✅ Build vector embeddings for data retrieval
- ✅ Create conversational chat interface
- ✅ Integrate LLM responses with financial data

---

## Architecture

```
User Query
    ↓
Chat Interface (Streamlit)
    ↓
RAG Pipeline:
    1. Retrieve relevant data context from PostgreSQL
    2. Embed context using LLM embeddings
    3. Search vector database for similar context
    4. Build prompt with retrieved context
    ↓
Ollama Local LLM
    ↓
Generate Response with data context
    ↓
Display in Chat UI
```

---

## Getting Started

### Step 1: Start Ollama Service

```bash
# Start Ollama with Docker Compose
docker-compose up -d ollama

# Wait for it to be ready
sleep 10

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Step 2: Pull LLM Models

```bash
# Initialize Ollama and pull models
bash scripts/init_ollama.sh

# Or manually pull specific model
curl -X POST http://localhost:11434/api/pull -d '{"name":"mistral"}'

# Wait for download (may take a few minutes)
# Verify model is available
curl http://localhost:11434/api/tags
```

### Step 3: Install Phase 5 Dependencies

```bash
# Install LLM/RAG packages
uv sync --extra phase1 --extra phase2 --extra phase3 --extra phase5

# Or all at once
uv sync --extra all
```

### Step 4: Test LLM Connection

```bash
# Test Ollama API endpoint
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "mistral",
    "prompt": "What is the capital of France?",
    "stream": false
  }'

# Should return a response like:
# {"response":"Paris is the capital of France","done":true}
```

### Step 5: Run RAG Chat Interface

```bash
# Make sure all services are running
docker-compose up -d

# Run Streamlit
uv run streamlit run app/main.py

# Navigate to "AI Analyst" page (06_Assistant_Chat.py)
```

---

## Key Concepts

### 1. Large Language Models (LLMs)

**What is an LLM?**  
Neural network trained on massive amounts of text data. Can generate human-like text given a prompt.

**Local vs Cloud:**
- **Local (Ollama):** Runs on your machine, no API calls, privacy-friendly, slower
- **Cloud (OpenAI, Claude):** Fast, powerful, costs money, data sent to external servers

**Common Models:**
- Mistral (7B) - Fast, good quality, recommended for local
- Llama 2 (7B/13B/70B) - Meta's open-source model
- Neural Chat - Optimized for chat
- CodeLlama - Optimized for code generation

### 2. RAG (Retrieval-Augmented Generation)

**What is RAG?**  
Pattern that combines:
1. **Retrieval:** Find relevant data from your database
2. **Augmentation:** Include retrieved data in the prompt
3. **Generation:** LLM generates response based on data context

**Why RAG?**
- LLMs hallucinate without context (make up fake data)
- RAG grounds LLM responses in real data
- Enables Q&A on your specific dataset
- Updates without retraining the model

**Example:**

Without RAG:
```
User: "What was AAPL's close price on 2026-05-15?"
LLM: "I don't have access to real-time data, I was trained until April 2024"
```

With RAG:
```
User: "What was AAPL's close price on 2026-05-15?"
System: Retrieves from DB: "AAPL close: $189.50 on 2026-05-15"
Prompt: "Based on this data: AAPL close: $189.50 on 2026-05-15, answer: What was AAPL's close price?"
LLM: "AAPL's close price on 2026-05-15 was $189.50"
```

### 3. Ollama

**What is Ollama?**  
Local LLM runtime. Download and run models locally without cloud APIs.

**Key Features:**
- Pull pre-trained models (`ollama pull mistral`)
- Run inference: `ollama run mistral "prompt"`
- REST API: `curl http://localhost:11434/api/generate`
- No GPU required (but faster with GPU)

**Available Models:**
```bash
# List available models
ollama list

# Pull new model
ollama pull mistral
ollama pull neural-chat
ollama pull dolphin-mixtral
```

### 4. Vector Embeddings

**What are Embeddings?**  
Convert text into vector (array of numbers). Similar texts → similar vectors.

**Use in RAG:**
- Convert data and user queries to vectors
- Find similar vectors using similarity search
- Retrieve most relevant data for RAG

**Libraries:**
- OpenAI Embeddings (cloud)
- Hugging Face Transformers (local)
- LangChain (abstraction)

---

## TODO: Implement Phase 5

### RAG Chat Engine (app/core/rag/chat_engine.py)

- [ ] **Ollama Connection**
  - Connect to local Ollama at `http://localhost:11434`
  - Handle model errors and timeouts
  - Support multiple models

- [ ] **Data Retrieval**
  - Query PostgreSQL for relevant financial data
  - Convert queries to SQL (e.g., "AAPL last week" → SQL query)
  - Retrieve context for RAG

- [ ] **Embedding & Vector Search**
  - Generate embeddings for retrieved data
  - Store in vector database (optional: Chroma, Weaviate)
  - Find most similar data to user query

- [ ] **Prompt Building**
  - Build system prompt with instructions
  - Add retrieved context to user prompt
  - Format for LLM consumption

- [ ] **Response Generation**
  - Call Ollama with prompt
  - Stream responses (optional)
  - Handle errors gracefully

- [ ] **Chat History**
  - Store conversation history
  - Use context from previous messages
  - Implement memory (last N messages)

### Chat Interface (06_Assistant_Chat.py)

- [ ] **Chat UI**
  - Text input for user questions
  - Display chat history
  - Show LLM response

- [ ] **Data Context Display**
  - Show retrieved data that informed response
  - Display relevant tables/charts
  - Build trust in AI response

- [ ] **Sample Queries**
  - Buttons for common questions:
    - "What stocks are trending today?"
    - "Which symbol has highest volatility?"
    - "Show me oversold symbols"
  - Help users learn what to ask

- [ ] **Settings**
  - Select LLM model
  - Adjust response temperature (creativity)
  - Set data retrieval parameters

---

## Example Implementation

### Chat Engine Function

```python
# app/core/rag/chat_engine.py

def chat_with_rag(query: str, model: str = "mistral") -> dict:
    """
    Main RAG chat function.
    
    Args:
        query: User question
        model: LLM model to use
    
    Returns:
        dict with response, data_context, sources
    """
    # 1. Retrieve data context
    context = retrieve_data_context(query)
    
    # 2. Build RAG prompt
    system_prompt = f"""
You are a financial analysis assistant. You have access to stock price and technical indicator data.
Use the provided data to answer user questions accurately. If data doesn't answer the question, say so.

Retrieved Data Context:
{context}
"""
    
    # 3. Call Ollama LLM
    response = call_ollama(system_prompt, query, model)
    
    # 4. Return response with sources
    return {
        "response": response,
        "data_context": context,
        "model": model
    }


def retrieve_data_context(query: str, limit: int = 5) -> str:
    """
    Retrieve relevant financial data based on query.
    
    TODO: Parse user query and execute relevant SQL
    - "AAPL price" → SELECT * FROM fct_daily_prices WHERE symbol = 'AAPL'
    - "which stocks are up today" → SELECT * FROM fct_daily_prices WHERE date = TODAY
    - "volatility" → SELECT * FROM fct_technical_indicators ...
    """
    # For now, return mock data
    return """
Recent AAPL Data:
- Date: 2026-05-17, Close: $189.75, Volume: 50.2M
- Date: 2026-05-16, Close: $189.50, Volume: 48.3M
- 7-day change: +1.2%
- Moving Average (20): $188.90
- RSI: 62 (neutral)
"""


def call_ollama(system_prompt: str, user_query: str, model: str = "mistral") -> str:
    """
    Call local Ollama LLM.
    """
    import requests
    
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": f"{system_prompt}\n\nUser: {user_query}\nAssistant:",
        "stream": False,
        "temperature": 0.7,
    }
    
    response = requests.post(url, json=payload, timeout=60)
    result = response.json()
    
    return result.get("response", "Error generating response")
```

### Streamlit Chat Interface

```python
# app/views/06_Assistant_Chat.py

import streamlit as st
from app.core.rag.chat_engine import chat_with_rag

st.title("🤖 AI Analyst")

# Model selection
model = st.sidebar.selectbox("Select Model", ["mistral", "neural-chat", "dolphin-mixtral"])

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Sample queries
st.sidebar.write("### Quick Queries")
if st.sidebar.button("📈 What's trending today?"):
    user_query = "Which stocks are showing the strongest uptrend today?"
else:
    user_query = None

# User input
if user_input := st.chat_input("Ask about stock data..."):
    user_query = user_input

# Process query
if user_query:
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    with st.chat_message("user"):
        st.write(user_query)
    
    # Get RAG response
    with st.spinner("Thinking..."):
        result = chat_with_rag(user_query, model)
    
    # Display response
    with st.chat_message("assistant"):
        st.write(result["response"])
        
        # Show data context in expander
        with st.expander("📊 Data Context"):
            st.code(result["data_context"], language="sql")
    
    # Add to history
    st.session_state.chat_history.append({"role": "assistant", "content": result["response"]})
```

---

## RAG Best Practices

### 1. Context Retrieval Strategy

```python
# Good: Retrieve specific data
query = "SELECT * FROM fct_daily_prices WHERE date >= CURRENT_DATE - INTERVAL '7 days'"

# Bad: Retrieve all data
query = "SELECT * FROM fct_daily_prices"  # Too much, LLM context window limited
```

### 2. Prompt Engineering

```python
# Good: Clear, specific prompt
prompt = """
You are a financial analyst. Use only the provided data to answer questions.
If data doesn't contain the answer, say "I don't have that data".

Data:
- AAPL close on 2026-05-17: $189.75
- MSFT close on 2026-05-17: $425.30

User question: Which stock had higher price on 2026-05-17?
"""

# Bad: Vague prompt
prompt = "What do you know about stocks?"
```

### 3. Error Handling

```python
try:
    response = call_ollama(prompt, model="mistral")
except requests.exceptions.ConnectionError:
    response = "Error: Ollama not running. Start with: docker-compose up ollama"
except requests.exceptions.Timeout:
    response = "Error: LLM request timed out. Try again."
```

---

## Troubleshooting

### Issue: "Connection refused" to Ollama
**Solution:**
```bash
# Check if Ollama is running
docker-compose ps ollama

# If not running, start it
docker-compose up -d ollama

# Wait for startup
sleep 10

# Test endpoint
curl http://localhost:11434/api/tags
```

### Issue: Model not found error
**Solution:**
```bash
# Pull the model
curl -X POST http://localhost:11434/api/pull -d '{"name":"mistral"}'

# Wait for download to complete
# List models
curl http://localhost:11434/api/tags
```

### Issue: LLM responses are hallucinating (making up data)
**Solution:**
- Add more specific context to RAG prompt
- Use smaller temperature value (e.g., 0.3 instead of 0.7)
- Filter retrieved data to only relevant records
- Add "If data doesn't contain the answer, say 'I don't know'" to system prompt

### Issue: Chat interface is slow
**Solution:**
- Use smaller, faster model (Mistral 7B)
- Stream responses (show output as it generates)
- Cache repeated queries
- Limit context size

---

## Advanced: Stream Responses

Instead of waiting for full LLM response, show it as it generates:

```python
import requests
import streamlit as st

@st.cache_data
def stream_ollama_response(prompt: str, model: str = "mistral"):
    """Stream LLM response."""
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True  # Enable streaming
    }
    
    response = requests.post(url, json=payload, stream=True)
    
    full_response = ""
    placeholder = st.empty()
    
    for line in response.iter_lines():
        chunk = line.decode('utf-8')
        if chunk:
            import json
            data = json.loads(chunk)
            token = data.get("response", "")
            full_response += token
            placeholder.write(full_response)
    
    return full_response
```

---

## Next Steps After Phase 5

Congratulations! You've completed the full data engineering learning path! 🎉

### What You've Learned:

- **Phase 1:** Real-time data ingestion (Streamlit + yfinance)
- **Phase 2:** Pipeline orchestration (Airflow + PostgreSQL)
- **Phase 3:** Data transformations (dbt)
- **Phase 4:** Analytics & dashboards (SQL + Plotly)
- **Phase 5:** AI integration (LLM + RAG)

### Future Learning:

- ✨ Advanced dbt: incremental models, snapshots, dynamic SQL
- ✨ ML/AI: time series forecasting, anomaly detection
- ✨ Data governance: data quality frameworks, lineage tracking
- ✨ Performance: query optimization, caching strategies
- ✨ DevOps: CI/CD for data pipelines, infrastructure as code
- ✨ Real-time: streaming data (Kafka, Spark Streaming)

### Build a Real Project:

Take these skills and build your own data pipeline! Ideas:
- Cryptocurrency dashboard with alerts
- Social media sentiment analysis
- Weather forecasting
- Sports analytics
- Real estate price predictions

---

**Congratulations on completing de-bootcamp-summer2026!** 🚀

You're now equipped with a modern data engineering toolkit. Keep learning and building! 📊
