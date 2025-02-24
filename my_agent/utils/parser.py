from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
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


class Answer(BaseModel):
    pretext: str = Field(description="Textual Response, can be detailed if the card is not needed")
    Card: Optional[List[Union[PropertyCard, RichContent]]] = Field(description="JSON object with all the details that will be used to render the card")

parser = JsonOutputParser(pydantic_object=Answer)

