"""
Dataset metadata catalog for data.gov.in agricultural and climate datasets.
This module maintains a curated list of known datasets with their API indices,
fields, and metadata to enable intelligent query routing.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class DatasetMetadata:
    """Metadata for a data.gov.in dataset"""
    dataset_id: str
    name: str
    description: str
    source: str
    category: str
    api_resource_id: str
    fields: List[str]
    update_frequency: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dataset_id': self.dataset_id,
            'name': self.name,
            'description': self.description,
            'source': self.source,
            'category': self.category,
            'api_resource_id': self.api_resource_id,
            'fields': self.fields,
            'update_frequency': self.update_frequency,
            'tags': self.tags
        }


class DatasetsCatalog:
    """Centralized catalog of agriculture and climate datasets from data.gov.in"""
    
    def __init__(self):
        self.datasets: Dict[str, DatasetMetadata] = {}
        self._initialize_catalog()
    
    def _initialize_catalog(self):
        """Initialize catalog with known agriculture and climate datasets"""
        
        datasets = [
            DatasetMetadata(
                dataset_id="crop_production",
                name="Crop Production Statistics",
                description="State and district-level crop production data including area, production, and yield",
                source="Ministry of Agriculture & Farmers Welfare",
                category="agriculture",
                api_resource_id="9ef84268-d588-465a-a308-a864a43d0070",
                fields=["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production", "Yield"],
                update_frequency="Annual",
                tags=["crop", "production", "agriculture", "state", "district", "yield", "area"]
            ),
            DatasetMetadata(
                dataset_id="rainfall_india",
                name="Rainfall in India",
                description="Month-wise and subdivision-wise rainfall data with departure from normal",
                source="India Meteorological Department (IMD), Pune",
                category="climate",
                api_resource_id="7fbec2fc-85cd-4aec-851d-f473e57a2981",
                fields=["SUBDIVISION", "YEAR", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "ANNUAL", "Jan-Feb", "Mar-May", "Jun-Sep", "Oct-Dec"],
                update_frequency="Monthly",
                tags=["rainfall", "climate", "weather", "monsoon", "precipitation", "imd"]
            ),
            DatasetMetadata(
                dataset_id="district_rainfall",
                name="District-wise Rainfall",
                description="District-level rainfall data across India",
                source="India Meteorological Department (IMD)",
                category="climate",
                api_resource_id="d6a903fd-9f3e-4c6d-b1e1-e8c7b8f5a8d2",
                fields=["DIST_NAME", "STATE_NAME", "YEAR", "MONTH", "RAINFALL"],
                update_frequency="Monthly",
                tags=["rainfall", "district", "climate", "weather"]
            ),
            DatasetMetadata(
                dataset_id="agricultural_prices",
                name="Agricultural Commodity Prices",
                description="Farm harvest prices and wholesale prices of agricultural commodities",
                source="Ministry of Agriculture & Farmers Welfare",
                category="agriculture",
                api_resource_id="a8c8f8e0-3b2d-4f5e-9a1b-2c3d4e5f6a7b",
                fields=["State", "District", "Market", "Commodity", "Variety", "Grade", "Arrival_Date", "Min_Price", "Max_Price", "Modal_Price"],
                update_frequency="Daily",
                tags=["prices", "market", "commodity", "agriculture"]
            ),
            DatasetMetadata(
                dataset_id="irrigation_statistics",
                name="Irrigation Statistics",
                description="State-wise irrigation coverage and water resource utilization",
                source="Ministry of Agriculture & Farmers Welfare",
                category="agriculture",
                api_resource_id="b9d9e9f1-4c3e-5f6e-0b2c-3d4e5f6a7b8c",
                fields=["State_Name", "Year", "Net_Irrigated_Area", "Gross_Irrigated_Area", "Canal", "Tank", "Tubewell", "Other_Sources"],
                update_frequency="Annual",
                tags=["irrigation", "water", "agriculture", "resources"]
            ),
            DatasetMetadata(
                dataset_id="temperature_data",
                name="Temperature Data",
                description="State and district-level temperature data including min, max, and mean temperatures",
                source="India Meteorological Department (IMD)",
                category="climate",
                api_resource_id="c0e0f0g2-5d4f-6g7h-1c3d-4e5f6a7b8c9d",
                fields=["STATE", "DISTRICT", "YEAR", "MONTH", "MIN_TEMP", "MAX_TEMP", "MEAN_TEMP"],
                update_frequency="Monthly",
                tags=["temperature", "climate", "weather", "imd"]
            ),
            DatasetMetadata(
                dataset_id="soil_health",
                name="Soil Health Card Data",
                description="Soil testing data including pH, nutrients, and recommendations",
                source="Ministry of Agriculture & Farmers Welfare",
                category="agriculture",
                api_resource_id="d1f1g1h3-6e5g-7h8i-2d4e-5f6a7b8c9d0e",
                fields=["State", "District", "Village", "Farmer_Name", "Soil_Type", "pH", "Nitrogen", "Phosphorus", "Potassium", "Recommendations"],
                update_frequency="Ongoing",
                tags=["soil", "health", "nutrients", "agriculture"]
            ),
            DatasetMetadata(
                dataset_id="horticulture_production",
                name="Horticulture Production",
                description="State-wise production of fruits, vegetables, flowers, and plantation crops",
                source="Ministry of Agriculture & Farmers Welfare",
                category="agriculture",
                api_resource_id="e2g2h2i4-7f6h-8i9j-3e5f-6a7b8c9d0e1f",
                fields=["State", "Year", "Crop_Type", "Crop_Name", "Area", "Production", "Productivity"],
                update_frequency="Annual",
                tags=["horticulture", "fruits", "vegetables", "production", "agriculture"]
            )
        ]
        
        for dataset in datasets:
            self.datasets[dataset.dataset_id] = dataset
    
    def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """Get dataset metadata by ID"""
        return self.datasets.get(dataset_id)
    
    def search_datasets(self, query: str) -> List[DatasetMetadata]:
        """Search datasets by query string matching against tags, name, and description"""
        query_lower = query.lower()
        results = []
        
        for dataset in self.datasets.values():
            if (query_lower in dataset.name.lower() or
                query_lower in dataset.description.lower() or
                any(query_lower in tag for tag in dataset.tags)):
                results.append(dataset)
        
        return results
    
    def get_datasets_by_category(self, category: str) -> List[DatasetMetadata]:
        """Get all datasets in a category (agriculture, climate, etc.)"""
        return [d for d in self.datasets.values() if d.category == category]
    
    def get_datasets_by_tags(self, tags: List[str]) -> List[DatasetMetadata]:
        """Get datasets that match any of the provided tags"""
        results = []
        tags_lower = [t.lower() for t in tags]
        
        for dataset in self.datasets.values():
            if any(tag in dataset.tags for tag in tags_lower):
                results.append(dataset)
        
        return results
    
    def get_all_datasets(self) -> List[DatasetMetadata]:
        """Get all datasets in the catalog"""
        return list(self.datasets.values())
    
    def get_catalog_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the catalog"""
        categories = {}
        for dataset in self.datasets.values():
            categories[dataset.category] = categories.get(dataset.category, 0) + 1
        
        return {
            'total_datasets': len(self.datasets),
            'categories': categories,
            'datasets': [d.to_dict() for d in self.datasets.values()]
        }
