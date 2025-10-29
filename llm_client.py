"""
LLM client for query understanding and answer synthesis using Gemini.
This module uses the blueprint:python_gemini integration.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel

# IMPORTANT: KEEP THIS COMMENT
# Follow these instructions when using this blueprint:
# - Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
#   - do not change this unless explicitly requested by the user

# This API key is from Gemini Developer API Key, not vertex AI API Key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


class QueryUnderstanding(BaseModel):
    """Structured output for query understanding"""
    intent: str
    required_datasets: List[str]
    filters: Dict[str, Any]
    aggregations: List[str]
    comparison_needed: bool
    time_range: Optional[Dict[str, Any]]


class LLMClient:
    """Client for LLM-powered query understanding and answer synthesis"""
    
    def __init__(self):
        """Initialize the LLM client"""
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        self.model_flash = "gemini-2.5-flash"
        self.model_pro = "gemini-2.5-pro"
        self.max_retries = 3
        self.retry_delay = 2
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff for handling API overload errors
        
        Args:
            func: Function to retry
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Result from the function
        
        Raises:
            Exception: If all retries fail
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                if '503' in error_str or 'overloaded' in error_str.lower() or 'UNAVAILABLE' in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                
                raise e
        
        if last_error:
            raise last_error
        
        raise Exception("Unexpected error: all retries exhausted without exception")
    
    def understand_query(
        self,
        user_query: str,
        available_datasets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Understand user query and determine which datasets and operations are needed
        
        Args:
            user_query: The user's natural language question
            available_datasets: List of available dataset metadata
        
        Returns:
            Dictionary with query understanding results
        """
        datasets_info = "\n".join([
            f"- {d['dataset_id']}: {d['name']} ({d['description']})\n  Tags: {', '.join(d['tags'])}"
            for d in available_datasets
        ])
        
        prompt = f"""You are an expert data analyst helping users query Indian agricultural and climate data.

Available datasets:
{datasets_info}

User question: {user_query}

Analyze this question and provide:
1. The intent/goal of the query
2. Which datasets are needed (use dataset_id values)
3. What filters should be applied (e.g., state names, crop types, year ranges)
4. What aggregations are needed (e.g., sum, average, count)
5. Whether comparisons between entities are needed
6. The time range involved (if mentioned)

Respond in JSON format:
{{
    "intent": "brief description of what user wants",
    "required_datasets": ["dataset_id1", "dataset_id2"],
    "filters": {{"field_name": "value"}},
    "aggregations": ["operation description"],
    "comparison_needed": true/false,
    "time_range": {{"start_year": 2010, "end_year": 2020}} or null
}}"""
        
        try:
            def _make_request():
                return client.models.generate_content(
                    model=self.model_flash,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            
            response = self._retry_with_backoff(_make_request)
            
            if response.text:
                result = json.loads(response.text)
                return result
            else:
                return {
                    'intent': user_query,
                    'required_datasets': [],
                    'filters': {},
                    'aggregations': [],
                    'comparison_needed': False,
                    'time_range': None
                }
            
        except Exception as e:
            return {
                'intent': user_query,
                'required_datasets': [],
                'filters': {},
                'aggregations': [],
                'comparison_needed': False,
                'time_range': None,
                'error': str(e)
            }
    
    def synthesize_answer(
        self,
        user_query: str,
        data_results: Dict[str, Any],
        dataset_citations: List[Dict[str, str]]
    ) -> str:
        """
        Synthesize a comprehensive answer from data results
        
        Args:
            user_query: The original user question
            data_results: Dictionary containing fetched and processed data
            dataset_citations: List of datasets used with their sources
        
        Returns:
            Formatted answer with citations
        """
        data_summary = json.dumps(data_results, indent=2, default=str)
        citations_text = "\n".join([
            f"- {c['name']} (Source: {c['source']})"
            for c in dataset_citations
        ])
        
        prompt = f"""You are an expert data analyst providing insights on Indian agricultural and climate data.

User Question: {user_query}

Retrieved Data:
{data_summary}

Data Sources Used:
{citations_text}

Instructions:
1. Provide a clear, comprehensive answer to the user's question based ONLY on the data provided
2. Use specific numbers and statistics from the data
3. If comparisons were requested, clearly present them
4. If trends were asked about, describe them with data points
5. For policy questions, provide data-backed arguments
6. IMPORTANT: For every claim or statistic you mention, add a citation in [brackets] referring to the data source
7. If the data is insufficient to answer the question fully, state what's missing
8. Keep the answer well-structured with sections if the question is complex

Format your answer in markdown with proper headings, bullet points, and citations."""
        
        try:
            def _make_request():
                return client.models.generate_content(
                    model=self.model_pro,
                    contents=prompt
                )
            
            response = self._retry_with_backoff(_make_request)
            
            return response.text or "Unable to generate answer from the data provided."
            
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Extract entities like state names, crop names, years from query
        
        Args:
            query: User's natural language query
        
        Returns:
            Dictionary of entity types and their values
        """
        prompt = f"""Extract specific entities from this agricultural/climate query:

Query: {query}

Identify and extract:
- States (Indian state names)
- Districts (district names)
- Crops (crop names or crop types)
- Years (specific years or year ranges)
- Seasons (Kharif, Rabi, Summer, etc.)
- Climate parameters (rainfall, temperature, etc.)

Respond in JSON format:
{{
    "states": ["state1", "state2"],
    "districts": ["district1"],
    "crops": ["crop1", "crop2"],
    "years": [2020, 2021],
    "seasons": ["Kharif"],
    "climate_params": ["rainfall"]
}}

Only include entities that are explicitly mentioned. Use empty lists for missing entities."""
        
        try:
            def _make_request():
                return client.models.generate_content(
                    model=self.model_flash,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            
            response = self._retry_with_backoff(_make_request)
            
            if response.text:
                return json.loads(response.text)
            else:
                return {
                    'states': [],
                    'districts': [],
                    'crops': [],
                    'years': [],
                    'seasons': [],
                    'climate_params': []
                }
            
        except Exception as e:
            return {
                'states': [],
                'districts': [],
                'crops': [],
                'years': [],
                'seasons': [],
                'climate_params': [],
                'error': str(e)
            }
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a concise summary of text"""
        prompt = f"Summarize this in {max_length} characters or less:\n\n{text}"
        
        try:
            response = client.models.generate_content(
                model=self.model_flash,
                contents=prompt
            )
            return response.text or text[:max_length]
        except Exception as e:
            return text[:max_length]
