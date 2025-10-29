"""
Query orchestrator that coordinates between LLM, datasets catalog, and data fetching.
This is the core intelligence that determines what data to fetch and how to combine it.
"""

from typing import Dict, List, Any, Optional, Tuple
from datasets_catalog import DatasetsCatalog, DatasetMetadata
from datagov_client import DataGovClient
from llm_client import LLMClient
import json


class QueryOrchestrator:
    """Orchestrates the entire query processing pipeline"""
    
    def __init__(self):
        """Initialize the orchestrator with all required components"""
        self.catalog = DatasetsCatalog()
        self.data_client = None
        self.llm_client = None
        self.citations = []
    
    def initialize_clients(self):
        """Initialize API clients (called after API keys are available)"""
        try:
            self.data_client = DataGovClient()
            self.llm_client = LLMClient()
            return True
        except ValueError as e:
            return False
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query end-to-end
        
        Args:
            user_query: The user's natural language question
        
        Returns:
            Dictionary with answer, citations, and metadata
        """
        if not self.data_client or not self.llm_client:
            return {
                'success': False,
                'error': 'API clients not initialized. Please configure API keys.',
                'answer': 'Unable to process query without API keys.',
                'citations': [],
                'data_used': {}
            }
        
        self.citations = []
        
        try:
            all_datasets = self.catalog.get_all_datasets()
            datasets_info = [d.to_dict() for d in all_datasets]
            
            understanding = self.llm_client.understand_query(user_query, datasets_info)
            
            entities = self.llm_client.extract_entities(user_query)
            
            data_results = self._fetch_required_data(understanding, entities)
            
            dataset_citations = self._build_citations(understanding['required_datasets'])
            
            answer = self.llm_client.synthesize_answer(
                user_query,
                data_results,
                dataset_citations
            )
            
            return {
                'success': True,
                'answer': answer,
                'citations': dataset_citations,
                'query_understanding': understanding,
                'entities_extracted': entities,
                'data_used': data_results,
                'datasets_queried': understanding['required_datasets']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': user_query,
                'answer': f'An error occurred while processing your query: {str(e)}',
                'citations': [],
                'data_used': {}
            }
    
    def _fetch_required_data(
        self,
        understanding: Dict[str, Any],
        entities: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Fetch data from required datasets based on query understanding
        
        Args:
            understanding: Query understanding from LLM
            entities: Extracted entities from query
        
        Returns:
            Dictionary containing fetched data organized by dataset
        """
        results = {}
        
        for dataset_id in understanding.get('required_datasets', []):
            dataset = self.catalog.get_dataset(dataset_id)
            if not dataset:
                continue
            
            filters = self._build_filters(dataset, understanding, entities)
            
            if not self.data_client:
                continue
            
            try:
                data = self.data_client.fetch_data(
                    resource_id=dataset.api_resource_id,
                    filters=filters,
                    limit=1000
                )
                
                if data['success'] and data['records']:
                    processed_data = self._process_data(
                        data['records'],
                        understanding,
                        entities,
                        dataset
                    )
                    
                    results[dataset_id] = {
                        'dataset_name': dataset.name,
                        'record_count': len(data['records']),
                        'data': processed_data,
                        'source': dataset.source
                    }
                else:
                    results[dataset_id] = {
                        'dataset_name': dataset.name,
                        'record_count': 0,
                        'data': [],
                        'error': data.get('error', 'No records found'),
                        'source': dataset.source
                    }
                    
            except Exception as e:
                results[dataset_id] = {
                    'dataset_name': dataset.name,
                    'error': str(e),
                    'source': dataset.source
                }
        
        return results
    
    def _build_filters(
        self,
        dataset: DatasetMetadata,
        understanding: Dict[str, Any],
        entities: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Build API filters based on dataset fields and extracted entities"""
        filters = {}
        
        field_mappings = {
            'State_Name': entities.get('states', []),
            'STATE_NAME': entities.get('states', []),
            'SUBDIVISION': entities.get('states', []),
            'STATE': entities.get('states', []),
            'State': entities.get('states', []),
            'District_Name': entities.get('districts', []),
            'DISTRICT': entities.get('districts', []),
            'DIST_NAME': entities.get('districts', []),
            'Crop': entities.get('crops', []),
            'Crop_Name': entities.get('crops', []),
            'YEAR': entities.get('years', []),
            'Year': entities.get('years', []),
            'Crop_Year': entities.get('years', []),
            'Season': entities.get('seasons', [])
        }
        
        for field in dataset.fields:
            if field in field_mappings and field_mappings[field]:
                filters[field] = field_mappings[field][0]
        
        if understanding.get('filters'):
            filters.update(understanding['filters'])
        
        return filters
    
    def _process_data(
        self,
        records: List[Dict[str, Any]],
        understanding: Dict[str, Any],
        entities: Dict[str, List[str]],
        dataset: DatasetMetadata
    ) -> Any:
        """Process and aggregate data based on query requirements"""
        
        if not understanding.get('aggregations'):
            return records[:50]
        
        if 'average' in str(understanding.get('aggregations', [])).lower():
            return self._compute_averages(records, entities, dataset)
        elif 'sum' in str(understanding.get('aggregations', [])).lower() or 'total' in str(understanding.get('aggregations', [])).lower():
            return self._compute_totals(records, entities, dataset)
        elif 'comparison' in str(understanding.get('aggregations', [])).lower() or understanding.get('comparison_needed'):
            return self._prepare_comparison(records, entities, dataset)
        else:
            return records[:50]
    
    def _compute_averages(
        self,
        records: List[Dict[str, Any]],
        entities: Dict[str, List[str]],
        dataset: DatasetMetadata
    ) -> Dict[str, Any]:
        """Compute averages from records"""
        from collections import defaultdict
        
        if 'rainfall' in dataset.dataset_id or 'climate' in dataset.category:
            return self._average_climate_data(records)
        elif 'crop' in dataset.dataset_id or 'agriculture' in dataset.category:
            return self._average_agriculture_data(records)
        
        return {'records': records[:20]}
    
    def _average_climate_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Average climate data (rainfall, temperature)"""
        from collections import defaultdict
        
        data_by_location = defaultdict(list)
        
        for record in records:
            location = (record.get('SUBDIVISION') or record.get('STATE_NAME') or 
                       record.get('STATE') or record.get('DIST_NAME') or 'Unknown')
            
            for key, value in record.items():
                if key not in ['SUBDIVISION', 'STATE_NAME', 'STATE', 'DIST_NAME', 'YEAR', 'MONTH']:
                    try:
                        data_by_location[location].append({
                            'parameter': key,
                            'value': float(value),
                            'year': record.get('YEAR'),
                            'month': record.get('MONTH')
                        })
                    except (ValueError, TypeError):
                        continue
        
        averages = {}
        for location, values in data_by_location.items():
            param_values = defaultdict(list)
            for item in values:
                param_values[item['parameter']].append(item['value'])
            
            averages[location] = {
                param: sum(vals) / len(vals) if vals else 0
                for param, vals in param_values.items()
            }
        
        return {'averages_by_location': averages, 'record_count': len(records)}
    
    def _average_agriculture_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Average agriculture data (production, area, yield)"""
        from collections import defaultdict
        
        data_by_crop = defaultdict(lambda: {'production': [], 'area': [], 'yield': []})
        
        for record in records:
            crop = record.get('Crop') or record.get('Crop_Name') or 'Unknown'
            
            if record.get('Production'):
                try:
                    data_by_crop[crop]['production'].append(float(record['Production']))
                except (ValueError, TypeError):
                    pass
            
            if record.get('Area'):
                try:
                    data_by_crop[crop]['area'].append(float(record['Area']))
                except (ValueError, TypeError):
                    pass
            
            if record.get('Yield'):
                try:
                    data_by_crop[crop]['yield'].append(float(record['Yield']))
                except (ValueError, TypeError):
                    pass
        
        averages = {}
        for crop, data in data_by_crop.items():
            averages[crop] = {
                'avg_production': sum(data['production']) / len(data['production']) if data['production'] else 0,
                'avg_area': sum(data['area']) / len(data['area']) if data['area'] else 0,
                'avg_yield': sum(data['yield']) / len(data['yield']) if data['yield'] else 0,
                'record_count': len(data['production'])
            }
        
        return {'averages_by_crop': averages}
    
    def _compute_totals(self, records: List[Dict[str, Any]], entities: Dict[str, List[str]], dataset: DatasetMetadata) -> Dict[str, Any]:
        """Compute totals from records"""
        totals = {}
        
        numeric_fields = ['Production', 'Area', 'ANNUAL', 'RAINFALL']
        
        for field in numeric_fields:
            values = []
            for record in records:
                if field in record:
                    try:
                        values.append(float(record[field]))
                    except (ValueError, TypeError):
                        continue
            
            if values:
                totals[field] = {
                    'total': sum(values),
                    'average': sum(values) / len(values),
                    'count': len(values)
                }
        
        return {'totals': totals, 'record_count': len(records)}
    
    def _prepare_comparison(self, records: List[Dict[str, Any]], entities: Dict[str, List[str]], dataset: DatasetMetadata) -> Dict[str, Any]:
        """Prepare data for comparison"""
        comparison_data = {}
        
        group_field = None
        if 'State_Name' in dataset.fields or 'STATE_NAME' in dataset.fields:
            group_field = 'State_Name' if 'State_Name' in dataset.fields else 'STATE_NAME'
        elif 'SUBDIVISION' in dataset.fields:
            group_field = 'SUBDIVISION'
        elif 'District_Name' in dataset.fields:
            group_field = 'District_Name'
        
        if group_field:
            from collections import defaultdict
            grouped = defaultdict(list)
            
            for record in records:
                key = record.get(group_field)
                if key:
                    grouped[key].append(record)
            
            comparison_data['grouped_by'] = group_field
            comparison_data['groups'] = {k: v[:10] for k, v in grouped.items()}
        else:
            comparison_data['records'] = records[:50]
        
        return comparison_data
    
    def _build_citations(self, dataset_ids: List[str]) -> List[Dict[str, str]]:
        """Build citation information for datasets used"""
        citations = []
        
        for dataset_id in dataset_ids:
            dataset = self.catalog.get_dataset(dataset_id)
            if dataset:
                citations.append({
                    'dataset_id': dataset.dataset_id,
                    'name': dataset.name,
                    'source': dataset.source,
                    'description': dataset.description,
                    'url': f'https://data.gov.in/resource/{dataset.api_resource_id}'
                })
        
        return citations
    
    def get_available_datasets_summary(self) -> str:
        """Get a summary of available datasets for display"""
        summary = self.catalog.get_catalog_summary()
        
        text = f"**Available Datasets: {summary['total_datasets']}**\n\n"
        text += f"**Categories:** {', '.join(f'{k} ({v})' for k, v in summary['categories'].items())}\n\n"
        text += "**Datasets:**\n"
        
        for dataset in summary['datasets']:
            text += f"\n- **{dataset['name']}** ({dataset['category']})\n"
            text += f"  - {dataset['description']}\n"
            text += f"  - Source: {dataset['source']}\n"
        
        return text
