"""
Data.gov.in API client for fetching agricultural and climate data.
Handles API authentication, data fetching, filtering, and caching.
"""

import os
import requests
import time
from typing import Dict, List, Any, Optional
from functools import lru_cache
import json


class DataGovClient:
    """Client for interacting with data.gov.in API"""
    
    BASE_URL = "https://api.data.gov.in/resource"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client with API key
        
        Args:
            api_key: data.gov.in API key (if not provided, reads from environment)
        """
        self.api_key = api_key or os.environ.get('DATA_GOV_IN_API_KEY')
        if not self.api_key:
            raise ValueError("DATA_GOV_IN_API_KEY must be provided or set as environment variable")
        
        self.session = requests.Session()
        self.cache = {}
    
    def fetch_data(
        self,
        resource_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
        sort: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch data from a specific resource
        
        Args:
            resource_id: The API resource ID for the dataset
            filters: Dictionary of field:value pairs to filter results
            limit: Maximum number of records to fetch
            offset: Starting record offset for pagination
            sort: Dictionary of field:order pairs for sorting
        
        Returns:
            Dictionary containing records and metadata
        """
        cache_key = self._generate_cache_key(resource_id, filters, limit, offset, sort)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        params = {
            'api-key': self.api_key,
            'format': 'json',
            'offset': offset,
            'limit': limit
        }
        
        if filters:
            for field, value in filters.items():
                params[f'filters[{field}]'] = value
        
        if sort:
            sort_params = []
            for field, order in sort.items():
                sort_params.append(f"{field}:{order}")
            params['sort'] = ','.join(sort_params)
        
        url = f"{self.BASE_URL}/{resource_id}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            result = {
                'records': data.get('records', []),
                'total': data.get('total', len(data.get('records', []))),
                'count': len(data.get('records', [])),
                'offset': offset,
                'limit': limit,
                'resource_id': resource_id,
                'success': True
            }
            
            self.cache[cache_key] = result
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                'records': [],
                'total': 0,
                'count': 0,
                'offset': offset,
                'limit': limit,
                'resource_id': resource_id,
                'success': False,
                'error': str(e)
            }
    
    def fetch_all_data(
        self,
        resource_id: str,
        filters: Optional[Dict[str, Any]] = None,
        max_records: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Fetch all available records from a dataset (with pagination)
        
        Args:
            resource_id: The API resource ID for the dataset
            filters: Dictionary of field:value pairs to filter results
            max_records: Maximum total records to fetch
        
        Returns:
            List of all records
        """
        all_records = []
        offset = 0
        limit = 1000
        
        while len(all_records) < max_records:
            result = self.fetch_data(resource_id, filters, limit, offset)
            
            if not result['success'] or not result['records']:
                break
            
            all_records.extend(result['records'])
            
            if result['count'] < limit:
                break
            
            offset += limit
            time.sleep(0.5)
        
        return all_records[:max_records]
    
    def query_with_fields(
        self,
        resource_id: str,
        fields: List[str],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query dataset and return only specific fields
        
        Args:
            resource_id: The API resource ID
            fields: List of field names to return
            filters: Filters to apply
            limit: Maximum records to fetch
        
        Returns:
            List of records with only requested fields
        """
        result = self.fetch_data(resource_id, filters, limit)
        
        if not result['success']:
            return []
        
        filtered_records = []
        for record in result['records']:
            filtered_record = {field: record.get(field) for field in fields if field in record}
            filtered_records.append(filtered_record)
        
        return filtered_records
    
    def aggregate_data(
        self,
        records: List[Dict[str, Any]],
        group_by: str,
        agg_field: str,
        agg_func: str = 'sum'
    ) -> Dict[str, float]:
        """
        Aggregate data by a field
        
        Args:
            records: List of data records
            group_by: Field to group by
            agg_field: Field to aggregate
            agg_func: Aggregation function (sum, avg, min, max, count)
        
        Returns:
            Dictionary mapping group values to aggregated values
        """
        from collections import defaultdict
        
        groups = defaultdict(list)
        
        for record in records:
            key = record.get(group_by)
            value = record.get(agg_field)
            
            if key and value is not None:
                try:
                    groups[key].append(float(value))
                except (ValueError, TypeError):
                    continue
        
        result = {}
        for key, values in groups.items():
            if agg_func == 'sum':
                result[key] = sum(values)
            elif agg_func == 'avg':
                result[key] = sum(values) / len(values)
            elif agg_func == 'min':
                result[key] = min(values)
            elif agg_func == 'max':
                result[key] = max(values)
            elif agg_func == 'count':
                result[key] = len(values)
        
        return result
    
    def _generate_cache_key(
        self,
        resource_id: str,
        filters: Optional[Dict[str, Any]],
        limit: int,
        offset: int,
        sort: Optional[Dict[str, str]]
    ) -> str:
        """Generate cache key for a request"""
        key_parts = [resource_id, str(limit), str(offset)]
        
        if filters:
            key_parts.append(json.dumps(filters, sort_keys=True))
        
        if sort:
            key_parts.append(json.dumps(sort, sort_keys=True))
        
        return '|'.join(key_parts)
    
    def clear_cache(self):
        """Clear the client cache"""
        self.cache.clear()
