import http.client
import json
import urllib
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import tool
from my_agent.utils.tool_utils import search_community_ID, search_school_ID, get_fips_codes,get_property_details, map_property_types_to_ids, map_property_availablity, get_property_search, extract_key_objects, get_api_headers
from urllib.parse import urlencode
from my_agent.utils.models.property_search import PropertySearchFields, PropertySearchInput

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re
import requests
import os

v1_url: str = os.environ["V1_URL"]
test_mode: str = os.environ["TEST_MODE"]
secret_key: str = os.environ["HAR_SECRET_KEY"]
token: str = os.environ["HAR_TOKEN"]

class PropertySearchResultItem(BaseModel):
    mlsnum: Optional[str]
    address: Optional[str]
    price: Optional[float]
    beds: int
    baths: int
    city: str
    zipCode: str
    sqft: int
#args_schema=PropertySearchFields
class AgentSearchInput(BaseModel):
    Name:str= Field(
        description="Agent Name to search properties or details about him/her"
    )    

class PropertySearchByAddress(BaseModel):
    address: Optional[str] = Field(
        None, description="List of addresses to search properties"
    )
    harid: Optional[int] = Field(None, description="List of harid to search properties")

@tool
def search_properties_by_address(
    obj: PropertySearchByAddress,
) -> dict[str, list[Any]]:
    """Search properties based on property address OR harid filter"""

    conn = http.client.HTTPSConnection("api.har.com")

    # Check if address or MLS number is provided and set appropriate endpoint and payload
    if obj.address:
        # Use quick search API if address is provided
        path = "/chatbot/quicksearch"
        payload = {"query": obj.address}
    elif obj.harid:
        # Use listing API directly if MLS number is provided
        path = f"/chatbot/property/{obj.harid}"
        payload = {}  # No payload needed for direct listing lookup
    else:
        raise ValueError("Either address or MLS number must be provided.")

    # Convert payload to query string if there are payload parameters
    if payload:
        query_string = "&".join([f"{k}={v}" for k, v in payload.items()])
        path += f"?{query_string}"

    json_response = None
    try:
        if obj.harid:
            json_response, _ = get_property_search(conn, path)

        # Handle quick search API response if an address was used
        elif obj.address:
            json_response, _ = get_property_search(conn, path)
            harids = [
                result.get("harid", None) for result in json_response.get("results", [])
            ]

            # Use the first MLS number to get listing details
            if harids:
                listing_path = f"/chatbot/property/{harids[0]}"
                json_response, _ = get_property_details(conn, listing_path)

    finally:
        conn.close()

    # Process the listing API response to extract required details
    if json_response.get("status", None) == "success":
        result, found_harid = extract_key_objects(json_response)
        return {
            "total_number_of_properties": 1 if found_harid else 0,
            "properties": result,
        }

    return {"total_number_of_properties": 0, "properties": []}

@tool(args_schema=AgentSearchInput)
def search_agent(Name: AgentSearchInput):
    """Search property agent based on name """    
    agent_detail = None
    conn = http.client.HTTPSConnection("api.har.com")
    path = f"/member?agent={Name}"
    timestamp = int((datetime.now() + timedelta(hours=2)).timestamp() * 1000)
    headers = get_api_headers(path, token, secret_key, timestamp, test_mode, "", "", "")
    path = path.replace(" ", "%20")
    conn.request("GET", path, "", headers)
    res = conn.getresponse()
    data = res.read()
    print(data, headers)
    # Convert the data to a JSON object
    agent_detail = json.loads(data.decode("utf-8"))
    return agent_detail

# Example use:
# Create an instance of PropertySearchFields with the desired search criteria
# search_criteria = PropertySearchFields(city=["Houston"], max_price=500000)
# properties = search_properties(fields=search_criteria)



@tool(args_schema=PropertySearchInput)
def search_properties(fields: PropertySearchFields) -> Dict[str, Any]:
    """
    Description: Search properties based on some input filters

    TEMPORAL CONTEXT:
        - Current reference year: 2025

    Guidelines:
        - [IMPORTANT] Analyze the user query carefully before assigning filters, dont confuse similar naming features.
        - Divide the user prompt and extract the features.
        - Invoke tool on show more each time , Analyze 'chat_history' to assign start filter a value, It should be incremented by 5 each time.
        - while using tool always add for_sale field into it with its value unless for_rent is specified.
        - To initialize filters for 'price', 'baths_bathrooms' and 'bedrooms_beds', it will be a dictionary with number with 'equal'[priority], 'min', 'max' as keys.
        - MANDATORY: For each query [INVOKE_TOOL=TRUE] → accumulate_all_previous_filters + add_new_valid_filters → MUST_EXECUTE_TOOL(complete_filter_set) → await_results before_response
    """

    
    # Getting user
    user = None #get_user()
    islogin = 0

    if user:
        user_id = str(user.get("userid", ""))
        role = 0
        islogin = 1
        role = int(user.get("roleid"))
        member_number = user.get("member_number", "")

        if role > 1:
            role = "realtor"
        else:
            role = "consumer"

    else:
        user_id = ""
        role = 0
        member_number = ""

    community_id = 0
    county = None
    bedroom_min = None
    bedroom_max = None
    bath_max = None
    bath_min = None
    price_min = None
    price_max = None
    schooldistrict = None
    eschool = None
    mschool = None
    hschool = None
    property_types = {
        "Single Family": "1",
        "Townhouse/Condo": "2",
        "High-Rise": "6",
        "Mid-Rise": "6",
        "Condominium": "6",  # Assuming 'Condominium' is the same as 'Mid / High-Rise'
        "Multi-Family": "4",
    }
    checker = []
    if fields.listed_today:
        fields.days_on_market_max = 1
    if fields.school_district:
        schooldistrict = search_school_ID(fields.school_district, type="D")
        checker.append(schooldistrict)
    if fields.elemantary_school:
        eschool = search_school_ID(fields.elemantary_school, type="E")
        checker.append(eschool)
    if fields.middle_school:
        mschool = search_school_ID(fields.middle_school, type="M")
        checker.append(mschool)
    if fields.high_school:
        hschool = search_school_ID(fields.high_school, type="H")
        checker.append(hschool)

    if fields.community:
        community_id = search_community_ID(fields.community[0])
        checker.append(community_id)
    if fields.county:
        county = get_fips_codes(fields.county)
        checker.append(county)

    if any(value is None for value in checker):
        return {
            "total_number_of_properties": 0,
            "start": 0,
            "stop": 0,
            "properties": None,
        }

    if fields.baths_bathrooms:
        if "min" in fields.baths_bathrooms:
            bath_min = fields.baths_bathrooms["min"]
        if "max" in fields.baths_bathrooms:
            bath_max = fields.baths_bathrooms["max"]
        if "equal" in fields.baths_bathrooms:
            bath_min = fields.baths_bathrooms["equal"]
            bath_max = fields.baths_bathrooms["equal"]

    if fields.bedrooms_beds:
        if "min" in fields.bedrooms_beds:
            bedroom_min = fields.bedrooms_beds["min"]
        if "max" in fields.bedrooms_beds:
            bedroom_max = fields.bedrooms_beds["max"]
        if "equal" in fields.bedrooms_beds:
            bedroom_max = fields.bedrooms_beds["equal"]
            bedroom_min = fields.bedrooms_beds["equal"]

    if fields.price:
        if "min" in fields.price:
            price_min = fields.price["min"]
        if "max" in fields.price:
            price_max = fields.price["max"]
        if "equal" in fields.price:
            price_max = fields.price["equal"]
            price_min = fields.price["equal"]

    payload = {
        "city": (
            ",".join(urllib.parse.quote(city, safe="!~*'()") for city in fields.city)
            if fields.city
            else None
        ),
        "fips_code": (
            ",".join(
                urllib.parse.quote(fips_code, safe="!~*'()") for fips_code in county
            )
            if county
            else None
        ),
        "subdivisions": fields.subdivisions,
        "zip_code": fields.zip_code,
        "mlsnum": fields.mls_number,
        "bedroom_min": bedroom_min,
        "bedroom_max": bedroom_max,
        "for_sale": 0 if not (fields.for_sale) else 1,
        "full_bath_min": bath_min,
        "full_bath_max": bath_max,
        "half_bath_num": fields.half_bath_num,
        "lotsize_min": fields.lotsize_min,
        "lotsize_max": fields.lotsize_max,
        "acres_min": fields.acres_min,
        "acres_max": fields.acres_max,
        "garage_num": fields.garage_num,
        "garage_desc": fields.garage_desc,
        "stories": (
            ",".join(str(story) for story in fields.stories) if fields.stories else None
        ),
        "new_constr": fields.new_constr,
        "parking": fields.parking,
        "listing_price_min": price_min,
        "listing_price_max": price_max,
        "property_class_id": (
            map_property_types_to_ids(fields.property_type)
            if fields.property_type
            else (property_types if fields.home_only else None)
        ),
        "max": fields.limit,
        "style": fields.style,
        "finance": fields.finance,
        "all_status": (
            map_property_availablity(fields.availablity)
            if fields.availablity and role == "realtor"
            else (
                ["N"]
                if fields.availablity
                and (
                    fields.availablity[0] == "term"
                    or fields.availablity[0] == "CS"
                    or fields.availablity[0] == "exp"
                    or fields.availablity[0] == "WITH"
                )
                and role != "realtor"
                else (None)
            )
        ),
        "sort": fields.sort,
        "start": fields.start,
        "price_sqft_min": fields.price_sqft_min,
        "price_sqft_max": fields.price_sqft_max,
        "square_feet_min": fields.square_feet_min,
        "square_feet_max": fields.square_feet_max,
        "hoa_fee_max": fields.hoa_fee_max,
        "community": community_id if community_id else None,
        "school_district": schooldistrict if schooldistrict else None,
        "schoolmiddle": mschool if mschool else None,
        "schoolelementary": eschool if eschool else None,
        "schoolhigh": hschool if hschool else None,
        # Amenities:
        "loft": 1 if fields.loft else None,
        "private_pool": (
            1 if fields.pool is True else (0 if fields.pool is False else None)
        ),
        "area_pool": 1 if fields.area_pool else None,
        "areatennis": 1 if fields.areatennis else None,
        "yard": 1 if fields.yard is True else None,
        "garageapt": 1 if fields.garageapt else None,
        "sprinkle": 1 if fields.sprinkle else None,
        "patiodeck": 1 if fields.patiodeck else None,
        "mediarm": 1 if fields.mediarm else None,
        "studyrm": 1 if fields.studyrm else None,
        "spahottub": 1 if fields.spahottub else None,
        "culdesac": 1 if fields.culdesac else None,
        "corner": 1 if fields.corner else None,
        "waterview": 1 if fields.waterview else None,
        "waterfront": 1 if fields.waterfront else None,
        "lake": 1 if fields.lake else None,
        # "dom": 1 if fields.listed_today is True else None,
        "stype": (
            1
            if fields.new_entry is True or "new_entry" in fields.quick_access
            else None
        ),
        "wooded": 1 if fields.wooded else None,
        "greenbelt": 1 if fields.greenbelt else None,
        "ongolfcourse": 1 if fields.ongolfcourse else None,
        "ingolfcom": 1 if fields.ingolfcom else None,
        "energy": 1 if fields.energy else None,
        "greencert": 1 if fields.greencert else None,
        "access": 1 if fields.access else None,
        "wheelchair": 1 if fields.wheelchair else None,
        "elevator": 1 if fields.elevator else None,
        "furnished": 1 if fields.furnished else None,
        # Extras
        "pricereduced": (
            1 if fields.pricereduced or "pricereduced" in fields.quick_access else None
        ),
        "forcl": 1 if fields.forcl or "forcl" in fields.quick_access else None,
        "new_constr2": (
            "Yes"
            if fields.new_constr2 or "new_constr2" in fields.quick_access
            else None
        ),
        "open_houses": (
            1 if fields.open_houses or "open_houses" in fields.quick_access else None
        ),
        "voh_only": 1 if fields.voh_only or "voh_only" in fields.quick_access else None,
        "year_built_min": fields.year_built_min,
        "year_built_max": fields.year_built_max,
        "DOM_MAX": fields.days_on_market_max,
        "DOM_MIN": fields.days_on_market_min,
        # Add more filters as needed...
    }

    conn = http.client.HTTPSConnection("api.har.com")
    path = "/listing"
    if fields.sold:
        path = "/sold"
    payload = {k: v for k, v in payload.items() if v is not None}

    # convert payload to query string and concatenate with path
    fullpath: str = path + "?" + "&".join([f"{k}={v}" for k, v in payload.items()])
    fullpath = fullpath.replace("%20", " ")

    try:
        json_response, _ = get_property_details(
            conn, fullpath, user_id, member_number, role
        )
    finally:
        conn.close()

    # Extract the share URL
    if fields.availablity is not None and len(fields.availablity) > 0:
        if fields.availablity[0] == "WITH":
            json_response = json_response.get("withdrawn", [])
        elif fields.availablity[0] == "term":
            json_response = json_response.get("terminate", [])
        elif fields.availablity[0] == "exp":
            json_response = json_response.get("expire", [])

    if fields.availablity is not None and len(fields.availablity) > 0:
        total = (
            int(json_response.get("total", 0))
            if json_response and json_response.get("total")
            else 0
        )
        start = (
            int(json_response.get("start", 0))
            if json_response and json_response.get("start")
            else 0
        )
        stop = (
            json_response.get("stop", 0)
            if json_response and json_response.get("stop")
            else 0
        )
        end = start + 5 if start > 0 else 5

        if (
            fields.availablity[0] == "WITH"
            or fields.availablity[0] == "term"
            or fields.availablity[0] == "exp"
        ):
            if json_response and json_response.get("listings"):
                results = json_response.get("listings", [])[start:end]
            else:
                results = []
        else:
            results = json_response.get("listings", [])
    else:
        total = int(json_response.get("total", 0))
        start = json_response.get("start")
        stop = json_response.get("stop")
        results = json_response.get("listings", [])

    properties = []
    for listing in results:
        # Date should be added in the api json_response
        # detail_obj = listing.get('detail', {})
        # date_str = detail_obj.get('date', None)
        # days=calculate_days(date_str)
        properties.append(
            {
                "id": listing.get("id", None),
                "status_short": listing.get("status_short", None),
                "mlsnum": listing.get("mlsnum", None),
                "harid": listing.get("harid", None),
                "share_url": listing.get("share_url", None),
                "address": listing.get("address", None),
                "price": float(listing.get("price", 0) or 0),
                "beds": int(listing.get("bed", 0) or 0),
                "bath": listing.get("bath", None),
                "city": listing.get("city", None),
                "zipCode": listing.get("zip", None),
                "sqft": int(listing.get("sqft", 0) or 0),
                "agent": listing.get("agent", None),
                "photo": listing.get("photo", None),
                "agentUrl": "/"
                + listing.get("agent").lower().replace(" ", "-")
                + "/agent_"
                + listing.get("agentlistid").lower(),
                "status": listing.get("status", None),
                "status_text": listing.get("status_text", None),
                "agentphoto": listing.get("agentphoto", None),
                "broker": listing.get("broker", None),
                "property_type": listing.get("propertytype", None),
                "bookmarked": listing.get("bookmarked", None),
                "islogin": islogin,
            }
        )

    return {
        "url": fullpath,
        "total_number_of_properties": total,
        "start": start,
        "stop": stop,
        "properties": properties,
    }

tools = [search_properties, search_agent]