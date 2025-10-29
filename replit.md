# Project Samarth

## Overview
Project Samarth is an intelligent Q&A system that queries live agricultural and climate data from data.gov.in (Indian Government's open data portal) to answer complex natural language questions about India's agricultural economy and climate patterns.

**Current State:** Fully functional MVP with all core features implemented

**Last Updated:** October 28, 2025

## Purpose
Enable policymakers, researchers, and analysts to derive cross-domain insights from government data using natural language queries, with AI-powered reasoning and complete source citations for accuracy and traceability.

## Recent Changes

### October 28, 2025 - Initial Build & Improvements
- Created complete intelligent Q&A system architecture
- Implemented dataset catalog with 8 curated agriculture and climate datasets
- Built data.gov.in API client with caching and filtering capabilities
- Integrated Gemini 2.5 Pro/Flash for query understanding and answer synthesis
- Created query orchestrator that determines datasets needed and coordinates retrieval
- Implemented citation tracking system linking every claim to data sources
- Built Streamlit chat interface with conversation history
- Added data preprocessing utilities for handling inconsistent formats
- Configured Gemini integration using blueprint:python_gemini
- **Added retry logic with exponential backoff** for handling Gemini API 503 overload errors
- **Improved error messaging** to provide user-friendly guidance when API is temporarily unavailable

## Core Features

### MVP Features (Completed)
1. **Interactive Chat Interface** - Natural language questions about agriculture and climate data
2. **Programmatic Data Fetching** - Live data from data.gov.in API with API key management
3. **AI-Powered Query Understanding** - LLM determines relevant datasets and required filters
4. **Multi-Dataset Integration** - Fetches and combines agriculture and climate data
5. **Intelligent Answer Generation** - LLM synthesizes cross-domain insights
6. **Source Citation System** - Tracks and displays data.gov.in references for every claim
7. **Complex Query Support** - Handles rainfall comparisons, crop production analysis, trend correlations, policy recommendations
8. **Data Caching Layer** - Reduces API calls and improves response times
9. **Clean Dashboard** - Query history and expandable source references

### Sample Questions Supported
- "Compare the average annual rainfall in Maharashtra and Karnataka for the last 5 years"
- "What are the top 3 most produced crops in Punjab?"
- "Analyze rice production trends in West Bengal over the last decade"
- "Which district in Uttar Pradesh has the highest wheat production?"
- "Correlate rainfall patterns with crop yields in Tamil Nadu"
- "Data-backed arguments for promoting drought-resistant crops in Rajasthan"

## Project Architecture

### Core Modules

1. **datasets_catalog.py** - Centralized catalog of 8 agriculture and climate datasets
   - DatasetMetadata: Stores dataset info (ID, name, description, API resource ID, fields, tags)
   - DatasetsCatalog: Search and retrieve dataset metadata by tags, category, or query

2. **datagov_client.py** - Data.gov.in API client
   - fetch_data(): Query datasets with filters, pagination, sorting
   - fetch_all_data(): Paginated retrieval of large datasets
   - aggregate_data(): Perform aggregations (sum, avg, min, max, count)
   - Caching layer to reduce API calls

3. **llm_client.py** - Gemini LLM integration
   - understand_query(): Analyze user question and determine required datasets
   - synthesize_answer(): Generate comprehensive answers with citations
   - extract_entities(): Extract states, crops, years, seasons from queries
   - _retry_with_backoff(): Automatic retry with exponential backoff for API overload (503 errors)
   - Uses gemini-2.5-pro for synthesis, gemini-2.5-flash for understanding
   - Handles temporary API failures gracefully with up to 3 retries

4. **query_orchestrator.py** - Core intelligence coordinator
   - process_query(): End-to-end query processing pipeline
   - _fetch_required_data(): Fetch from multiple datasets based on understanding
   - _build_filters(): Create API filters from extracted entities
   - _process_data(): Aggregate and prepare data (averages, totals, comparisons)
   - _build_citations(): Generate source citations

5. **data_preprocessing.py** - Data normalization and cleaning
   - normalize_state_name(): Standardize state names across datasets
   - normalize_crop_name(): Standardize crop names
   - clean_numeric_value(): Handle various numeric formats
   - standardize_field_names(): Unify field names across ministries
   - preprocess_dataset(): Clean entire datasets

6. **app.py** - Streamlit chat interface
   - Chat interface with message history
   - Sidebar with sample questions and dataset browser
   - Real-time query processing with spinner feedback
   - Expandable citations and query analysis
   - API key status checking

### Data Flow
1. User enters natural language question
2. LLM analyzes query to understand intent and extract entities (states, crops, years)
3. Orchestrator determines which datasets to query
4. API client fetches data from data.gov.in with appropriate filters
5. Preprocessor normalizes data formats
6. Orchestrator aggregates/processes data as needed
7. LLM synthesizes comprehensive answer with citations
8. UI displays answer with expandable source references

### Dataset Catalog (8 Datasets)

**Agriculture Datasets:**
- Crop Production Statistics (area, production, yield by state/district)
- Agricultural Commodity Prices (market prices)
- Irrigation Statistics (irrigation coverage)
- Horticulture Production (fruits, vegetables)
- Soil Health Card Data (nutrients, pH)

**Climate Datasets:**
- Rainfall in India (monthly, subdivision-wise)
- District-wise Rainfall
- Temperature Data (min, max, mean)

## Configuration

### Required API Keys (Environment Variables)
- `DATA_GOV_IN_API_KEY` - From https://www.data.gov.in (register and get from "My Account")
- `GEMINI_API_KEY` - From https://aistudio.google.com/apikey

### Streamlit Configuration
Located in `.streamlit/config.toml`:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

### Workflow
Command: `streamlit run app.py --server.port 5000`
Output: webview (Streamlit interface)

## Dependencies
- streamlit - Web interface
- google-genai - Gemini LLM integration
- requests - HTTP client for data.gov.in API
- pydantic - Data validation

## User Preferences
None specified yet

## Technical Decisions

### Why Gemini over OpenAI/Anthropic?
User requested Gemini API key availability. Using gemini-2.5-pro for answer synthesis (higher quality) and gemini-2.5-flash for query understanding (faster).

### Why In-Memory Caching?
For MVP, simple dictionary-based cache in DataGovClient reduces redundant API calls. Future: Redis or persistent cache.

### Why 8 Curated Datasets?
Started with most relevant datasets for sample questions. System designed to easily add more datasets to catalog.

### Why No Database?
Session-based chat application. Query history stored in Streamlit session state. No need for cross-session persistence in MVP.

## Data Sovereignty & Privacy
- All data sources are from public government APIs
- No user data is stored permanently
- System can be deployed in private/secure environments
- API keys managed through environment variables
- No data sent to external services except LLM for processing

## Known Limitations
1. Dataset catalog is manually curated (8 datasets)
2. Some data.gov.in API resource IDs may need verification
3. Data quality depends on government portal updates
4. LLM costs per query (Gemini API usage)
5. No visualization capabilities yet (planned for future)
6. No export functionality yet (planned for future)

## Future Enhancements (Next Phase)
1. Advanced data preprocessing for more inconsistent formats
2. Semantic search across dataset metadata for auto-discovery
3. Visualization capabilities (charts, graphs)
4. Export functionality (PDF, CSV)
5. User feedback loop for improving accuracy
6. Expand dataset catalog to 50+ datasets
7. Support for regional language queries

## Troubleshooting

### API Keys Not Configured
- Check Secrets panel has DATA_GOV_IN_API_KEY and GEMINI_API_KEY
- Restart workflow after adding secrets

### No Data Returned
- Verify dataset API resource IDs are correct
- Check data.gov.in portal is accessible
- Review filters being applied in query analysis

### LLM Errors
- Check GEMINI_API_KEY is valid
- Verify API quota limits not exceeded
- Review query complexity

## Testing
System supports complex multi-dataset queries:
- Cross-state rainfall comparisons
- Crop production rankings
- Climate-agriculture correlations
- Policy recommendation analysis

All answers include source citations for verification.
