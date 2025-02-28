from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, root_validator
from langchain_openai import ChatOpenAI
from typing import List, Optional, Dict, Union
# Define your desired data structure.

class PropertyCard(BaseModel):
    Image: str  
    Address: str  
    id: str  
    status_short: str  
    mlsnum: str  
    harid: str  
    share_url: str  
    address: str  
    price: float  
    beds: int  
    bath: str  
    city: str  
    zipCode: str  
    sqft: int  
    agent: str  
    photo: str  
    agentUrl: str  
    status: str  
    status_text: str  
    agentphoto: str  
    broker: str  
    property_type: str  
    bookmarked: bool  
    islogin: bool  


class RichContent(BaseModel):
    Image: str
    Name: str
    URL: str

class SchoolCard(BaseModel):
    Image: str
    Name: str
    DistrictName: str
    Address: str
    Grades: str
    ID: str
    RatingLetter: str
    RatingText: str
    URL: str
    
class AgentCard(BaseModel):
    Image: str
    Name: str
    Email: str
    AgentId: str
    ContactNo: str
    URL: str
    Rating: str

class Answer(BaseModel):
    pretext: str = Field(description="Textual Response, should be detailed if the card is gonna be null")
    Card: Optional[List[Union[PropertyCard, SchoolCard,AgentCard]]] = Field(description="JSON object with all the details that will be used to render the card")

from copy import deepcopy

def get_schema(state):
    """Determine the appropriate schema based on the last message's name."""
    
    base_schema = Answer.schema(ref_template="{model}")  # Get the full schema
    
    if state.get("messages") and state["messages"][-1].name in {"search_properties_by_address", None}:
        schema_copy = deepcopy(base_schema)  # Use deepcopy to avoid modifying the original
        
        # Remove PropertyCard from "Card" field
        schema_copy["properties"]["Card"]["items"]["anyOf"] = [
            {"$ref": "#/definitions/SchoolCard"},
            {"$ref": "#/definitions/AgentCard"},
        ]
        
        # Remove PropertyCard from definitions
        schema_copy["definitions"].pop("PropertyCard", None)
        
        return schema_copy
    
    return base_schema  # Default schema
# Return the original schema if no filtering is needed

parser = JsonOutputParser(pydantic_object=Answer)

