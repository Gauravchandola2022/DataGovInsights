
"""
Project Samarth - Intelligent Q&A System for Indian Agricultural and Climate Data
A Streamlit-based chat interface for querying data.gov.in datasets with AI-powered analysis
"""
# from dotenv import load_dotenv
# load_dotenv()

import streamlit as st
import os
from query_orchestrator import QueryOrchestrator
from datetime import datetime


st.set_page_config(
    page_title="Project Samarth",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize session state variables"""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = QueryOrchestrator()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'api_keys_configured' not in st.session_state:
        st.session_state.api_keys_configured = False
    
    if 'show_datasets' not in st.session_state:
        st.session_state.show_datasets = False


def check_api_keys():
    """Check if required API keys are configured"""
    data_gov_key = os.environ.get('DATA_GOV_IN_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    return bool(data_gov_key and gemini_key)


def render_sidebar():
    """Render the sidebar with app info and controls"""
    with st.sidebar:
        st.title("🌾 Project Samarth")
        st.markdown("### Intelligent Q&A System")
        st.markdown("Query Indian agricultural and climate data using natural language")
        
        st.divider()
        
        api_keys_ok = check_api_keys()
        if api_keys_ok:
            st.success("✓ API Keys Configured")
            if not st.session_state.api_keys_configured:
                if st.session_state.orchestrator.initialize_clients():
                    st.session_state.api_keys_configured = True
                    st.rerun()
        else:
            st.error("⚠️ API Keys Missing")
            st.markdown("""
            **Required:**
            - `DATA_GOV_IN_API_KEY`
            - `GEMINI_API_KEY`
            
            Please add them in the Secrets section.
            """)
        
        st.divider()
        
        st.markdown("### 💡 Sample Questions")
        
        sample_questions = [
            "Compare the average annual rainfall in Maharashtra and Karnataka for the last 5 years",
            "What are the top 3 most produced crops in Punjab?",
            "Analyze rice production trends in West Bengal over the last decade",
            "Which district in Uttar Pradesh has the highest wheat production?"
        ]
        
        for i, question in enumerate(sample_questions):
            if st.button(f"📝 Q{i+1}", key=f"sample_{i}", use_container_width=True):
                st.session_state.sample_question = question
        
        st.divider()
        
        if st.button("📚 View Available Datasets", use_container_width=True):
            st.session_state.show_datasets = not st.session_state.show_datasets
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        st.markdown("### 📊 About")
        st.markdown("""
        This system queries live data from **data.gov.in** to answer questions about:
        - 🌾 Agricultural production
        - 🌧️ Climate & rainfall patterns
        - 📈 Crop trends & statistics
        - 🏛️ Policy insights
        
        All answers include source citations for traceability.
        """)


def render_message(message):
    """Render a chat message"""
    role = message['role']
    content = message['content']
    
    if role == 'user':
        with st.chat_message('user'):
            st.markdown(content)
    else:
        with st.chat_message('assistant'):
            st.markdown(content)
            
            if 'citations' in message and message['citations']:
                with st.expander("📚 Data Sources & Citations"):
                    for citation in message['citations']:
                        st.markdown(f"""
                        **{citation['name']}**
                        - Source: {citation['source']}
                        - Description: {citation['description']}
                        - [View Dataset]({citation['url']})
                        """)
                        st.divider()
            
            if 'metadata' in message and message['metadata']:
                with st.expander("🔍 Query Analysis"):
                    metadata = message['metadata']
                    
                    if 'query_understanding' in metadata:
                        st.markdown("**Intent:** " + metadata['query_understanding'].get('intent', 'N/A'))
                        st.markdown("**Datasets Used:** " + ", ".join(metadata.get('datasets_queried', [])))
                    
                    if 'entities_extracted' in metadata:
                        entities = metadata['entities_extracted']
                        if any(entities.values()):
                            st.markdown("**Extracted Entities:**")
                            for entity_type, values in entities.items():
                                if values and entity_type != 'error':
                                    st.markdown(f"- {entity_type}: {', '.join(map(str, values))}")


def process_query(user_query: str):
    """Process user query and get response"""
    if not st.session_state.api_keys_configured:
        return {
            'answer': "⚠️ **API keys not configured.** Please configure DATA_GOV_IN_API_KEY and GEMINI_API_KEY in the Secrets section to use this system.",
            'citations': [],
            'metadata': {}
        }
    
    with st.spinner("🔍 Analyzing query and fetching data..."):
        result = st.session_state.orchestrator.process_query(user_query)
    
    if result['success']:
        return {
            'answer': result['answer'],
            'citations': result.get('citations', []),
            'metadata': {
                'query_understanding': result.get('query_understanding'),
                'entities_extracted': result.get('entities_extracted'),
                'datasets_queried': result.get('datasets_queried', [])
            }
        }
    else:
        error_msg = result.get('error', 'Unknown error')
        
        if '503' in error_msg or 'overloaded' in error_msg.lower() or 'UNAVAILABLE' in error_msg:
            return {
                'answer': f"""⏳ **Gemini API is temporarily overloaded**

The AI service is experiencing high demand right now. The system has already tried multiple times with exponential backoff.

**What you can do:**
- ⏰ **Wait a moment** and try your question again in 30-60 seconds
- 🔄 **Retry** - The issue is usually temporary and resolves quickly
- 📝 **Simplify** - Try a shorter or more focused question

**Your question was:** {result.get('query', 'N/A')}

This is a temporary issue with Google's Gemini API capacity, not with the application itself.""",
                'citations': [],
                'metadata': {}
            }
        else:
            return {
                'answer': f"❌ **Error processing query:** {error_msg}\n\nPlease try rephrasing your question or check that the required datasets are available.",
                'citations': [],
                'metadata': {}
            }


def main():
    """Main application function"""
    initialize_session_state()
    render_sidebar()
    
    if st.session_state.show_datasets:
        st.title("📚 Available Datasets")
        datasets_summary = st.session_state.orchestrator.get_available_datasets_summary()
        st.markdown(datasets_summary)
        st.divider()
    
    st.title("🌾 Project Samarth")
    st.markdown("### Ask questions about Indian agricultural and climate data")
    
    if not check_api_keys():
        st.warning("⚠️ Please configure API keys in the sidebar to start using the system.")
    else:
        st.info("💡 Ask questions about crop production, rainfall patterns, agricultural trends, and policy insights. Use the sample questions in the sidebar to get started!")
    
    for message in st.session_state.messages:
        render_message(message)
    
    user_input = None
    if 'sample_question' in st.session_state:
        user_input = st.session_state.sample_question
        del st.session_state.sample_question
    
    prompt = st.chat_input("Ask a question about agriculture or climate data...")
    
    if prompt:
        user_input = prompt
    
    if user_input:
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        render_message(st.session_state.messages[-1])
        
        response = process_query(user_input)
        
        st.session_state.messages.append({
            'role': 'assistant',
            'content': response['answer'],
            'citations': response['citations'],
            'metadata': response['metadata'],
            'timestamp': datetime.now().isoformat()
        })
        
        render_message(st.session_state.messages[-1])
        
        st.rerun()


if __name__ == "__main__":
    main()
