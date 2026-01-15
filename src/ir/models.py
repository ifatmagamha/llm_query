from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field

class FilterCondition(BaseModel):
    field: str
    operator: str  # "eq", "gt", "lt", "contains", "in"
    value: Any

class AggregationStep(BaseModel):
    type: str  # "group", "count", "sum", "avg"
    field: Optional[str] = None
    group_by: Optional[str] = None

class QueryIR(BaseModel):
    """
    Intermediate Representation for NoSQL Queries.
    This abstraction allows the LLM to 'think' in a unified way before
    compiling to a specific dialect (Mongo JSON, Cypher, etc.).
    """
    intent: str = Field(..., description="FIND, AGGREGATE, TRAVERSAL, or MUTATION")
    
    # Target
    target_collection: str = Field(..., description="The main collection, table, or node label")
    
    # Selection
    filters: List[FilterCondition] = []
    
    # Projection
    return_fields: List[str] = []
    
    # Aggregation
    aggregations: List[AggregationStep] = []
    
    # Modifiers
    limit: Optional[int] = None
    sort_field: Optional[str] = None
    sort_order: str = "ASC"  # "ASC" or "DESC"
    
    # Safety
    is_safe: bool = True
