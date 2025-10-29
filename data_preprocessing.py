"""
Data preprocessing utilities to handle inconsistent formats and coded values
across different ministry datasets from data.gov.in
"""

from typing import Any, Dict, List, Optional
import re


class DataPreprocessor:
    """Handles preprocessing and normalization of data from different sources"""
    
    STATE_NAME_MAPPINGS = {
        'andhra pradesh': 'Andhra Pradesh',
        'arunachal pradesh': 'Arunachal Pradesh',
        'assam': 'Assam',
        'bihar': 'Bihar',
        'chhattisgarh': 'Chhattisgarh',
        'goa': 'Goa',
        'gujarat': 'Gujarat',
        'haryana': 'Haryana',
        'himachal pradesh': 'Himachal Pradesh',
        'jharkhand': 'Jharkhand',
        'karnataka': 'Karnataka',
        'kerala': 'Kerala',
        'madhya pradesh': 'Madhya Pradesh',
        'maharashtra': 'Maharashtra',
        'manipur': 'Manipur',
        'meghalaya': 'Meghalaya',
        'mizoram': 'Mizoram',
        'nagaland': 'Nagaland',
        'odisha': 'Odisha',
        'orissa': 'Odisha',
        'punjab': 'Punjab',
        'rajasthan': 'Rajasthan',
        'sikkim': 'Sikkim',
        'tamil nadu': 'Tamil Nadu',
        'telangana': 'Telangana',
        'tripura': 'Tripura',
        'uttar pradesh': 'Uttar Pradesh',
        'uttarakhand': 'Uttarakhand',
        'west bengal': 'West Bengal',
        'andaman and nicobar islands': 'Andaman and Nicobar Islands',
        'chandigarh': 'Chandigarh',
        'dadra and nagar haveli': 'Dadra and Nagar Haveli',
        'daman and diu': 'Daman and Diu',
        'delhi': 'Delhi',
        'lakshadweep': 'Lakshadweep',
        'puducherry': 'Puducherry',
        'jammu and kashmir': 'Jammu and Kashmir',
        'ladakh': 'Ladakh'
    }
    
    CROP_NAME_MAPPINGS = {
        'paddy': 'Rice',
        'rice': 'Rice',
        'wheat': 'Wheat',
        'jowar': 'Sorghum',
        'bajra': 'Pearl Millet',
        'maize': 'Maize',
        'ragi': 'Finger Millet',
        'sugarcane': 'Sugarcane',
        'cotton': 'Cotton',
        'jute': 'Jute',
        'gram': 'Chickpea',
        'tur': 'Pigeon Pea',
        'arhar': 'Pigeon Pea',
        'moong': 'Green Gram',
        'urad': 'Black Gram',
        'masoor': 'Lentil',
        'groundnut': 'Groundnut',
        'peanut': 'Groundnut',
        'soyabean': 'Soybean',
        'soybean': 'Soybean',
        'sunflower': 'Sunflower',
        'safflower': 'Safflower',
        'rapeseed': 'Rapeseed and Mustard',
        'mustard': 'Rapeseed and Mustard',
        'potato': 'Potato',
        'onion': 'Onion',
        'tomato': 'Tomato'
    }
    
    SEASON_MAPPINGS = {
        'kharif': 'Kharif',
        'rabi': 'Rabi',
        'summer': 'Summer',
        'zaid': 'Summer',
        'whole year': 'Whole Year',
        'annual': 'Whole Year',
        'winter': 'Rabi',
        'monsoon': 'Kharif'
    }
    
    @staticmethod
    def normalize_state_name(state: str) -> str:
        """Normalize state names to standard format"""
        if not state:
            return ''
        
        state_lower = state.strip().lower()
        return DataPreprocessor.STATE_NAME_MAPPINGS.get(state_lower, state.strip().title())
    
    @staticmethod
    def normalize_crop_name(crop: str) -> str:
        """Normalize crop names to standard format"""
        if not crop:
            return ''
        
        crop_lower = crop.strip().lower()
        return DataPreprocessor.CROP_NAME_MAPPINGS.get(crop_lower, crop.strip().title())
    
    @staticmethod
    def normalize_season(season: str) -> str:
        """Normalize season names"""
        if not season:
            return ''
        
        season_lower = season.strip().lower()
        return DataPreprocessor.SEASON_MAPPINGS.get(season_lower, season.strip().title())
    
    @staticmethod
    def clean_numeric_value(value: Any) -> Optional[float]:
        """Clean and convert numeric values, handling various formats"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            value = value.strip()
            
            if not value or value.lower() in ['na', 'n/a', 'null', 'none', '-', '']:
                return None
            
            value = value.replace(',', '')
            
            value = re.sub(r'[^\d.-]', '', value)
            
            try:
                return float(value)
            except ValueError:
                return None
        
        return None
    
    @staticmethod
    def standardize_field_names(record: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize field names across different datasets"""
        field_mappings = {
            'state_name': 'State_Name',
            'statename': 'State_Name',
            'state': 'State_Name',
            'district_name': 'District_Name',
            'districtname': 'District_Name',
            'district': 'District_Name',
            'crop_name': 'Crop',
            'cropname': 'Crop',
            'crop_year': 'Year',
            'cropyear': 'Year',
            'year': 'Year',
            'season_name': 'Season',
            'seasonname': 'Season',
            'season': 'Season',
            'area_hectares': 'Area',
            'area': 'Area',
            'production_tonnes': 'Production',
            'production': 'Production',
            'yield_kg_per_hectare': 'Yield',
            'yield': 'Yield',
            'rainfall_mm': 'Rainfall',
            'rainfall': 'Rainfall',
            'temperature_celsius': 'Temperature',
            'temperature': 'Temperature',
            'temp': 'Temperature'
        }
        
        standardized = {}
        for key, value in record.items():
            key_lower = key.lower().strip()
            standard_key = field_mappings.get(key_lower, key)
            standardized[standard_key] = value
        
        return standardized
    
    @staticmethod
    def preprocess_record(record: Dict[str, Any], dataset_type: str = 'general') -> Dict[str, Any]:
        """
        Preprocess a single data record
        
        Args:
            record: Raw data record
            dataset_type: Type of dataset (agriculture, climate, general)
        
        Returns:
            Preprocessed record
        """
        processed = DataPreprocessor.standardize_field_names(record)
        
        if 'State_Name' in processed:
            processed['State_Name'] = DataPreprocessor.normalize_state_name(processed['State_Name'])
        
        if 'Crop' in processed:
            processed['Crop'] = DataPreprocessor.normalize_crop_name(processed['Crop'])
        
        if 'Season' in processed:
            processed['Season'] = DataPreprocessor.normalize_season(processed['Season'])
        
        numeric_fields = ['Area', 'Production', 'Yield', 'Rainfall', 'Temperature', 
                         'MIN_TEMP', 'MAX_TEMP', 'MEAN_TEMP', 'ANNUAL']
        
        for field in numeric_fields:
            if field in processed:
                processed[field] = DataPreprocessor.clean_numeric_value(processed[field])
        
        return processed
    
    @staticmethod
    def preprocess_dataset(records: List[Dict[str, Any]], dataset_type: str = 'general') -> List[Dict[str, Any]]:
        """
        Preprocess multiple records
        
        Args:
            records: List of raw data records
            dataset_type: Type of dataset
        
        Returns:
            List of preprocessed records
        """
        return [DataPreprocessor.preprocess_record(record, dataset_type) for record in records]
    
    @staticmethod
    def merge_datasets(datasets: List[List[Dict[str, Any]]], merge_keys: List[str]) -> List[Dict[str, Any]]:
        """
        Merge multiple datasets on common keys
        
        Args:
            datasets: List of datasets to merge
            merge_keys: Keys to merge on (e.g., ['State_Name', 'Year'])
        
        Returns:
            Merged dataset
        """
        if not datasets:
            return []
        
        if len(datasets) == 1:
            return datasets[0]
        
        merged = {}
        
        for dataset in datasets:
            for record in dataset:
                key_values = tuple(record.get(k) for k in merge_keys)
                
                if key_values not in merged:
                    merged[key_values] = {}
                
                merged[key_values].update(record)
        
        return list(merged.values())
    
    @staticmethod
    def handle_missing_values(record: Dict[str, Any], strategy: str = 'drop') -> Optional[Dict[str, Any]]:
        """
        Handle missing values in a record
        
        Args:
            record: Data record
            strategy: How to handle missing values ('drop', 'zero', 'mean')
        
        Returns:
            Processed record or None if dropped
        """
        if strategy == 'drop':
            if any(v is None for v in record.values()):
                return None
            return record
        
        elif strategy == 'zero':
            return {k: (0 if v is None else v) for k, v in record.items()}
        
        else:
            return record
