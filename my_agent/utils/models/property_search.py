from pydantic.v1 import BaseModel, Field
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional, Dict, Union, Any
from utils.models.constants import DEFAULT_MAX_LISTINGS


class PropertySearchFields(BaseModel):
    city: Optional[List[str]] = Field(
        None,
        description="List of Cities to search properties (e.g., ['Houston', 'Dallas']), CAN NEVER BE A NUMBER",
    )
    community: Optional[List[str]] = Field(
        None,
        description="List of master plan Communities to search properties on. {Key Communities: cinco ranch, copperfield, eaglewood, canyon gate at brazon, clear lake city}",
    )
    county: Optional[List[str]] = Field(
        None,
        description="List of County to search properties on.{Key Counties: Anderson, Andrews, Baylor, Bee, etc }",
    )
    subdivisions: Optional[str] = Field(
        None, description="List of Subdivisions to search properties on."
    )
    zip_code: Optional[Union[str, List[str]]] = Field(
        None,
        description="Numeric Zip code to search properties by, (e.g., 77027, 77024). Zip codes usually start with '77'.",
    )
    mls_number: Optional[str] = Field(
        None,
        description="Alpha-Numeric code for a single property.",
    )
    bedrooms_beds: Optional[Dict[str, int]] = Field(
        None,
        description="Dictionary with Number of Bedrooms or beds with keys 'min', 'max', or 'equal'",
    )
    baths_bathrooms: Optional[Dict[str, int]] = Field(
        None,
        description="Dictionary with Number of Bathrooms or baths with keys 'min', 'max', or 'equal'",
    )
    price: Optional[Dict[str, int]] = Field(
        None,
        description="Dictionary with Price of property with keys 'min', 'max', or 'equal' ",
    )
    limit: Optional[int] = Field(
        DEFAULT_MAX_LISTINGS,
        description=f"Number of properties to return; max value is {DEFAULT_MAX_LISTINGS}",
    )
    sold: Optional[bool] = Field(None, description="Indicates if the property is sold")
    for_sale: Optional[int] = Field(
        1, description="Indicates if the property is on rent"
    )
    sort: Optional[str] = Field(
        "listdate desc",
        description="sortings of property, invoke in all case of cheapest,expensive,etc ('listprice asc', 'listprice desc', 'lotsize asc', 'lotsize desc','yearbuilt asc', 'yearbuilt desc)",
    )
    start: Optional[int] = Field(
        None,
        description=f"Starting index for fetching property listings. Increment by {DEFAULT_MAX_LISTINGS} EACH time more listings are requested (i.e 5, 10, 15, 20,...)",
    )
    days_on_market_min: Optional[int] = Field(
        None, description="Minimum number of days on market"
    )
    days_on_market_max: Optional[int] = Field(
        None, description="Maximum number of days on market or listed within the last"
    )
    half_bath_num: Optional[bool] = Field(
        None, description="Indicator of of half bathrooms in the property"
    )
    lotsize_min: Optional[int] = Field(
        None, description="Minimum lot size in square feet"
    )
    lotsize_max: Optional[int] = Field(
        None, description="Maximum lot size in square feet"
    )
    acres_min: Optional[int] = Field(None, description="Minimum lot size in Acres")
    acres_max: Optional[int] = Field(None, description="Maximum lot size in Acres")
    square_feet_min: Optional[int] = Field(
        None, description="Minimum square feet of the building / home."
    )
    square_feet_max: Optional[int] = Field(
        None, description="Maximum square feet of the building / home."
    )

    acres_min: Optional[float] = Field(None, description="Minimum acreage")
    garage_num: Optional[int] = Field(
        None, description="garage spaces. Do not use for bedrooms or beds."
    )
    garage_desc: Optional[str] = Field(
        None,
        description="Description of the garage ['Attached', 'Detached', 'Tandem', 'Oversized', 'Attached/Detached']",
    )
    stories: Optional[List[float]] = Field(
        None, description="Number of stories (e.g., '1,1.5,2,3')"
    )
    new_constr: Optional[str] = Field(
        None, description="Indicates if the property is new construction ('Y' or 'N')"
    )
    parking: Optional[int] = Field(None, description="Number of parking spaces")
    property_type: Optional[List[str]] = Field(
        None,
        description="List of property types ('Single Family', 'Townhouse/Condo', 'Acreage', 'High-Rise','Mid-Rise', 'Condominium','Residential Lots', 'Multi-Family')",
    )
    year_built_min: Optional[int] = Field(
        None,
        description="Minimum year built. For properties built after a specific year, set this to that year + 1 (e.g., for homes built after 2011, set to 2012).",
    )
    year_built_max: Optional[int] = Field(
        None,
        description="Maximum year built, e.g., 'before 2020' should be set to 2019",
    )
    style: Optional[str] = Field(
        None,
        description="Style of property ('Contemporary', 'Colonial', 'French', 'Georgian', 'Ranch', 'Mediterranean', 'Spanish', 'Split Level', 'Traditional', 'Victorian')",
    )
    finance: Optional[List[str]] = Field(
        None,
        description="financial information ('Owner Financing','Lease/Purchase','Affordable Housing Program','Seller to Contribute to Buyer%27s Closing Costs','FHA','VA','Conventional')",
    )
    availablity: Optional[List[str]] = Field(
        None,
        description="Availablity information;  'Active' Available For Sale / For Rent Under Contract, 'OP' Option Pending Under Contract, 'PS'  Pending Continue to Show Under Contract, 'P' Under Contract Pending, 'closd' Sold Data, 'CS' Coming Soon, 'WITH' Withdrawn, 'term' Terminated, 'exp' Expired.",
    )
    quick_access: Optional[List[str]] = Field(
        [],
        description="List of Quick Access;   'pricereduced' price is reduced or price changes or price drops, 'forcl' property is Foreclosure, 'new_constr2' property is Newly constructed, 'open_houses' property has an open house, 'voh_only' property has virtual open house, 'new_entry' just listed or recently listed or this week",
    )
    price_sqft_min: Optional[int] = Field(
        None,
        description="Minimum 'Price per sqft' of the property, Only to be used when per sqft is used",
    )
    price_sqft_max: Optional[int] = Field(
        None,
        description="Maximum 'Price per sqft' of the property, Only to be used when per sqft is used",
    )
    hoa_fee_max: Optional[int] = Field(
        None,
        description="Low Maintenance fees per month is 10 or High Mentainance fees per month is 2500 or Low hoa fees is 10 or high hoa fees is 2500",
    )

    # Amenities:
    loft: Optional[bool] = Field(
        None, description="Indicates if the property has a loft"
    )
    pool: Optional[bool] = Field(
        None, description="Indicates if the property has a pool / private pool"
    )
    area_pool: Optional[bool] = Field(
        None, description="Indicates if the property has access to an area pool"
    )
    areatennis: Optional[bool] = Field(
        None, description="Indicates if the property has access to an area tennis court"
    )
    yard: Optional[bool] = Field(
        None, description="Indicates if the property has a yard"
    )
    garageapt: Optional[bool] = Field(
        None,
        description="Indicates if the property has a garage apartment/apt or guest house",
    )
    sprinkle: Optional[bool] = Field(
        None, description="Indicates if the property has a sprinkler system"
    )
    patiodeck: Optional[bool] = Field(
        None, description="Indicates if the property has a patio or deck"
    )
    mediarm: Optional[bool] = Field(
        None, description="Indicates if the property has a media room"
    )
    studyrm: Optional[bool] = Field(
        None, description="Indicates if the property has a Study Room or Home Office"
    )
    spahottub: Optional[bool] = Field(
        None, description="Indicates if the property has a spa or hot tub"
    )
    culdesac: Optional[bool] = Field(
        None, description="Indicates if the property is located on a cul-de-sac"
    )
    corner: Optional[bool] = Field(
        None, description="Indicates if the property is located on a corner"
    )
    waterview: Optional[bool] = Field(
        None, description="Indicates if the property has a water view"
    )
    waterfront: Optional[bool] = Field(
        None, description="Indicates if the property is on the waterfront"
    )
    lake: Optional[bool] = Field(
        None, description="Indicates if the property is near a lake"
    )
    wooded: Optional[bool] = Field(
        None, description="Indicates if the property is in a wooded area"
    )
    greenbelt: Optional[bool] = Field(
        None, description="Indicates if the property is near a greenbelt"
    )
    ongolfcourse: Optional[bool] = Field(
        None, description="Indicates if the property is on a golf course"
    )
    ingolfcom: Optional[bool] = Field(
        None, description="Indicates if the property is in a golf community"
    )
    energy: Optional[bool] = Field(
        None, description="Indicates if the property has energy-efficient features"
    )
    greencert: Optional[bool] = Field(
        None, description="Indicates if the property has a green certification"
    )
    access: Optional[bool] = Field(
        None,
        description="Indicates if the property has accessibility features or gated communities or gated community",
    )
    wheelchair: Optional[bool] = Field(
        None, description="Indicates if the property is wheelchair accessible"
    )
    elevator: Optional[bool] = Field(
        None, description="Indicates if the property has an elevator"
    )
    furnished: Optional[bool] = Field(
        None, description="Indicates if the property is furnished"
    )
    # Quick Access
    pricereduced: Optional[bool] = Field(
        None,
        description="Indicates if the property's price is reduced or price changes or price drops",
    )
    listed_today: Optional[bool] = Field(
        None,
        description="today or new listing today or listed today",
    )
    new_entry: Optional[bool] = Field(
        None,
        description="just listed or recently listed or this week",
    )
    forcl: Optional[bool] = Field(
        None, description="Indicates if the property is Foreclosure"
    )
    new_constr2: Optional[bool] = Field(
        None, description="Indicates if the property is Newly constructed"
    )
    open_houses: Optional[bool] = Field(
        None, description="Indicates if the property has an open house"
    )
    voh_only: Optional[bool] = Field(
        None, description="Indicates if the property has virtual open house"
    )
    # ignore these word in filters
    home_only: Optional[bool] = Field(
        None,
        description="Set to True when searching specifically for home or homes or house or houses or any homes or cheapest home",
    )
    school_district: Optional[str] = Field(
        None,
        description="School District to search property on (e.g., 'Katy ISD', 'Houston ISD', 'Spring Branch ISD')",
        examples=["Katy ISD", "Houston ISD"],
    )
    elemantary_school: Optional[str] = Field(
        None, description="Elementary School to search property on"
    )
    middle_school: Optional[str] = Field(
        None, description="Middle School to search property on"
    )
    high_school: Optional[str] = Field(
        None, description="High School to search property on"
    )


class PropertySearchInput(BaseModel):
    fields: PropertySearchFields = Field(
        ..., description="Input fields to search properties"
    )

    class Config:
        arbitrary_types_allowed = True  # Allows arbitrary types for fields
