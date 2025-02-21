
# Standard Library Imports
import os
import http.client
import json
import urllib.parse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re
import requests
import uuid
import pprint
from urllib.parse import urlencode

# Third-Party Imports
from dotenv import load_dotenv
from pydantic.v1 import BaseModel, Field
from langchain.callbacks import LangChainTracer
from langchain.callbacks.manager import CallbackManager

import hashlib


from my_agent.utils.models.constants import (
    DEFAULT_MAX_LISTINGS,
    API_SUCCESS_CODE,
    SESSION_KEY_PREFIX,
    CHAT_HISTORY_KEY_PREFIX,
    TTL_ONE_DAY,
    LLM_MODEL,
    REDIS_URL,
)
from langchain_core.runnables.utils import (
    ConfigurableFieldSpec,
)


# Load environment variables
load_dotenv()

# Environment variables
v1_url: str = os.environ["V1_URL"]
test_mode: str = os.environ["TEST_MODE"]
secret_key: str = os.environ["HAR_SECRET_KEY"]
token: str = os.environ["HAR_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
LANGCHAIN_TRACING_V2 = os.environ["LANGCHAIN_TRACING_V2"]
LANGCHAIN_API_KEY = os.environ["LANGCHAIN_API_KEY"]

tracer = LangChainTracer()
callback_manager = CallbackManager([tracer])


def get_api_headers(
    request_url: str,
    token: str,
    secretkey: str,
    timestamp: int,
    test_mode: str,
    user_id: Optional[str] = None,
    member_number: Optional[str] = None,
    role: Optional[str] = None,
) -> Dict[str, str]:
    baseurl = v1_url
    final = v1_url + request_url.replace("{{v1_url}}", "")

    pathinfo = (
        urllib.parse.quote(final.replace(baseurl, ""), safe="")
        .replace("%20", "+")
        .replace("(", "%28")
        .replace(")", "%29")
        .replace("*", "%2A")
        .replace("!", "%21")
        .replace("'", "%27")
    )

    hash_string = pathinfo + token + secretkey + str(timestamp)
    hash_md5 = hashlib.md5(hash_string.encode()).hexdigest()

    headers = {
        "X-Token": token,
        "X-Auth": hash_md5,
        "X-Expires": str(timestamp),
        "X-Test-Mode": test_mode,
        "X-App-Version": "4.0.0",
        "X-API-Version": "9",
    }

    if user_id:
        headers.update(
            {
                "X-Userid": user_id,
                "X-Realtorid": member_number,
                "X-User-Type": role,
                "X-App-Type": "web",
                "X-App-Name": "cb",
                "X-Device-Type": "windows",
                "X-App-Version": "4.0.0",
                "X-API-Version": "9",
            }
        )

        # Add headers if path matches
        if request_url.startswith("/chatbot/property/"):
            headers["X-UA"] = request.headers.get("User-Agent")
            headers["X-Page"] = request.url

    return headers


def search_community_ID(
    comm: str,
) -> dict[str, list[Any]]:
    """Search community ID using community name"""

    payload = {"query": comm}
    path = "http://har.com/api/typeapp/mpcfinder"
    community_id = None
    try:
        json_response, status_code = get_ID(path, payload)
        if status_code != API_SUCCESS_CODE:
            raise Exception(f"API Request failed with status code: {status_code}")

    except Exception as e:
        logging.error(f"Error fetching data for user query {path}: {e}")
        return {}
    if json_response:
        community_id = json_response[0]["community"]

    return community_id


def search_school_ID(school: str, type: str) -> str:
    """Search school ID using name"""
    payload = {"query": school, "type": type}
    path = "https://har.com/api/typeapp/schoolsearchfilter"
    id = None
    try:
        json_response, status_code = get_ID(path, payload)
        if status_code != API_SUCCESS_CODE:
            raise Exception(f"API Request failed with status code: {status_code}")

    except Exception as e:
        logging.error(f"Error fetching data for user query {path}: {e}")
        return {}
    if json_response:
        id = json_response[0]["base_id"]
    return id

def get_property_search(
    conn: http.client.HTTPSConnection, path: str
) -> Tuple[Dict[str, Any], int]:
    try:
        path = path.replace("#", "")
        timestamp = int((datetime.now() + timedelta(hours=2)).timestamp() * 1000)
        headers = get_api_headers(path, token, secret_key, timestamp, test_mode)

        # Make the request via http client
        path = path.replace(" ", "%20")
        # print(path)
        conn.request("GET", path, "", headers)
        res = conn.getresponse()
        data = res.read()

        # Convert the data to a JSON object
        json_data = json.loads(data.decode("utf-8"))

        # Raise appropriate exception if status code indicates an error
        # raise_for_status_code(res.status, json_data)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
        raise

    else:
        return json_data, res.status


class Community_Name(BaseModel):
    comm: Optional[str] = Field(None, description="Community Name")


def get_ID(path: str, payload: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    # Prepare the query parameters
    query_string = payload.get("query", "")
    type_string = payload.get("type", "")
    full_url = f"{path}?query={query_string}"
    if type_string:
        full_url = f"{full_url}&type={type_string}"

    # Add a User-Agent header to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Print the final URL for debugging purposes
    # print("Request URL:", full_url)

    # Make the GET request with headers
    response = requests.get(full_url, headers=headers)

    # Read the response and decode the JSON data
    if response.status_code == API_SUCCESS_CODE:
        json_data = response.json()
    else:
        json_data = {}
        print(f"Request failed with status code: {response.status_code}")

    return json_data, response.status_code

# agents.py


def calculate_days(date_str: str) -> int:
    try:
        date_format = "%Y-%m-%d %H:%M:%S"
        given_date = datetime.strptime(date_str, date_format)

        # Get the current date and time
        current_date = datetime.now()

        # Calculate the difference between the current date and the given date
        days = (current_date - given_date).days

    except ValueError as e:
        logging.error(f"Date parsing error")
        raise ValueError from e
    else:
        return days


def extract_all_tool_names(response: str) -> str:
    # Use a regex pattern to match the tool name from multiple 'AgentActionMessageLog(tool=...)' structures
    pattern = r"AgentActionMessageLog\(tool='([^']*)'"

    # Find all matches of the pattern in the response text
    matches = re.findall(pattern, str(response))

    # Return the list of all tool names found; if no matches, an empty list is returned
    return matches


def is_tool_invoked(agent_response: Dict[str, Any], tool_name: str) -> bool:
    # Assume extract_all_tool_names function is defined elsewhere and imported
    extracted_tools = extract_all_tool_names(agent_response)
    # Return True if the tool_name appears at least once in the list of extracted tools
    return tool_name in extracted_tools


def parse_selected_property_details(
    titles: list, values: list, keys_to_parse: list
) -> dict:
    parsed_data = {}
    if len(titles) == len(values) and len(titles) > 0:
        # Iterate through the titles and values and check only for requested keys
        for title, value in zip(titles, values):
            if title in keys_to_parse:
                # Ensure value is not None and check if it's a string before calling .strip()
                parsed_data[title] = (
                    value.strip() if isinstance(value, str) and value.strip() else None
                )
    return parsed_data


def extract_key_objects(
    api_response: Dict[str, Any],
) -> Tuple[list[Dict[str, Any]], bool]:
    try:
        # Handle detail and detailitems safely
        detail_obj = (
            api_response.get("detail", {}) or {}
        )  # Ensure it's a dict or fallback to empty
        detail_items = detail_obj.get("detailitems", {}) or {}

        titles = detail_items.get("titles", []) or []
        values = detail_items.get("values", []) or []

        # get driving directions
        driving_directions = ""
        # driving_directions = drivingDirections(api_response.get("mlsnum", None))

        # Check if "Bedrooms" exists in titles
        if "Bedrooms" in titles:
            index_of_bedrooms = titles.index("Bedrooms")
            bedrooms_value = values[index_of_bedrooms]
        else:
            bedrooms_value = None

        # Extract lease data
        extra = api_response.get("extra", {})

        if isinstance(extra, dict):
            lease = extra.get("lease", {})
            finance = extra.get("finance", {})
            if isinstance(lease, dict):
                lease_data = lease.get("data", [])
            else:
                lease_data = []
            if isinstance(finance, dict):
                finance_data = finance.get("data", [])
            else:
                finance_data = []
                lease_data = []
        else:
            finance_data = []
            lease_data = []  # Default to an empty list if "extra" is not a dictionary
        # Extract individual lease details
        application_fee = next(
            (
                item["Application Fee"]
                for item in lease_data
                if "Application Fee" in item
            ),
            None,
        )
        security_deposit = next(
            (
                item["Security Deposit"]
                for item in lease_data
                if "Security Deposit" in item
            ),
            None,
        )
        rental_terms = next(
            (item["Rental Terms"] for item in lease_data if "Rental Terms" in item),
            None,
        )
        rental_type = next(
            (item["Rental Type"] for item in lease_data if "Rental Type" in item), None
        )
        # Initialize variable to hold the result
        maint_fee_includes = None
        tax_rate = None
        tax_amount = None

        # Loop through the finance data to find "Maint Fee Includes"
        for item in finance_data:
            if "Maint Fee Includes" in item:
                maint_fee_includes = item["Maint Fee Includes"]
                break
        for item in finance_data:
            if "Tax Rate" in item:
                tax_rate = item["Tax Rate"]
                break

        for item in finance_data:
            if "Taxes W/o Exemp" in item:
                tax_amount = item["Taxes W/o Exemp"]
                break

        if detail_obj.get("type", None) == "value":
            keys_to_parse = [
                "Status",
                "Price/SQFT",
                "Bedrooms",
                "Baths",
                "Subdivision",
                "Year Built",
                "Lotsize",
                "Building SQFT",
                "Owner Name",
            ]
        else:
            keys_to_parse = [
                "Price per SQFT",
                "Property Type",
                "Bedrooms",
                "County",
                "Subdivision",
                "Legal Descriptio",
                "Garage",
                "Stories",
                "Style",
                "Baths",
                "Year Built",
                "Building Sqft",
                "Lotsize",
                "Acre(s)",
                "Maintenance Fee",
                "Market Area",
            ]

        inner_property_details = parse_selected_property_details(
            titles, values, keys_to_parse
        )

        # Extract sold-related details
        soldprice = detail_obj.get("soldprice", None)
        soldpricerange = detail_obj.get("soldpricerange", None)
        solddate = detail_obj.get("solddate", None)
        soldpricesqft = detail_obj.get("soldpricesqft", None)

        # Safely get realtor and broker data
        realtor = api_response.get("realtor", {}) or {}
        broker = api_response.get("broker", {}) or {}

        # Safely get photo URLs
        photos = api_response.get("photos", {}) or {}
        urls = photos.get("urls", []) or []

        # Check for first photo
        first_photo = urls[0] if urls else None

        outer_property_details = {
            "mlsnum": api_response.get("mlsnum", None),
            "harid": api_response.get("harid", None),
            "listing_date": detail_obj.get("date", None),
            "address": detail_obj.get("address", None),
            "price": float(detail_obj.get("price", 0) or 0),
            "beds": bedrooms_value,
            "shareurl": api_response.get("share_url", None),
            "city": detail_obj.get("city", None),
            "zipCode": detail_obj.get("zip", None),
            "sqft": int(detail_obj.get("sqft", 0) or 0),
            "agent": realtor.get("agentname", None),
            "agentphoto": realtor.get("photo", None),
            "agent_details": realtor,  # Avoid duplicate get
            "photo": first_photo,
            "status": detail_obj.get("status", None),
            "broker": broker.get("officename", None),
            "broker_details": broker,  # Avoid duplicate get
            "schools": api_response.get("schools", None),
            "sound_score": api_response.get("sound_score", None),
            "exterior": api_response.get("exterior", None),
            "interior": api_response.get("interior", None),
            "rooms": api_response.get("rooms", None),
            "rooms_metric": api_response.get("rooms_metric", None),
            "mortgage": api_response.get("mortgage", None),
            "openhouse": api_response.get("openhouse", None),
            "tax_details": api_response.get("tax", None),
            "neighborhood_info": api_response.get("neighborhoodinfo", None),
            "carmode": api_response.get("carmode", None),
            "virtual_tours": api_response.get("virtual_tours", None),
            "soldprice": soldprice,
            "soldpricerange": soldpricerange,
            "solddate": solddate,
            "soldpricesqft": soldpricesqft,
            "maint_fee_includes": maint_fee_includes,
            "application_fee": application_fee,
            "security_deposit": security_deposit,
            "rental_terms": rental_terms,
            "rental_type": rental_type,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "driving_directions": driving_directions,
        }

        properties = []
        properties.append(outer_property_details | inner_property_details)

        if properties[0].get("harid", None):
            found_harid = True
        else:
            found_harid = False

    except KeyError as e:
        raise KeyError from e
    else:
        return properties, found_harid


def get_property_details(
    conn: http.client.HTTPSConnection,
    path: str,
    user_id: Optional[str] = None,
    member_number: Optional[str] = None,
    role: Optional[int] = 0,
) -> Tuple[Dict[str, Any], int]:
    try:
        timestamp = int((datetime.now() + timedelta(hours=2)).timestamp() * 1000)
        headers = get_api_headers(
            path, token, secret_key, timestamp, test_mode, user_id, member_number, role
        )

        path = path.replace(" ", "%20")
        conn.request("GET", path, "", headers)
        res = conn.getresponse()
        data = res.read()

        # Convert the data to a JSON object
        json_data = json.loads(data.decode("utf-8"))

        # Raise appropriate exception if status code indicates an error
        # raise_for_status_code(res.status, json_data)

    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
        raise

    else:
        return json_data, res.status


def map_property_types_to_ids(property_types: List[str]) -> str:
    type_to_id = {
        "Single Family": "1",
        "Townhouse/Condo": "2",
        "Acreage": "5",
        "High-Rise": "6",
        "Mid-Rise": "6",
        "Condominium": "6",  # Assuming 'Condominium' is the same as 'Mid / High-Rise'
        "Residential Lots": "3",
        "Multi-Family": "4",
    }

    ids = [type_to_id[prop] for prop in property_types if prop in type_to_id]
    return ",".join(ids)


def map_property_availablity(property_types: List[str]) -> str:
    type_to_id = {
        "PS": "PS",
        "OP": "OP",
        "P": "P",
        "Available": "Available",
        "closd": "closd",
        "CS": "CS",
        "WITH": "WITH",
        "term": "term",
        "exp": "exp",
    }

    ids = [type_to_id[prop] for prop in property_types if prop in type_to_id]
    return ",".join(ids)


def get_fips_codes(county_names: List[str]) -> List[str]:
    """
    Returns a list of FIPS codes for the given list of county names.
    If a county name is not found in the map, `None` is returned for that entry.
    """
    # Original mapping: FIPS code => County name
    FIPS_MAP = {
        "48001": "Anderson",
        "48003": "Andrews",
        "48005": "Angelina",
        "48007": "Aransas",
        "48009": "Archer",
        "48011": "Armstrong",
        "48013": "Atascosa",
        "48015": "Austin",
        "48017": "Bailey",
        "48019": "Bandera",
        "48021": "Bastrop",
        "48023": "Baylor",
        "48025": "Bee",
        "48027": "Bell",
        "48029": "Bexar",
        "48031": "Blanco",
        "48033": "Borden",
        "48035": "Bosque",
        "48037": "Bowie",
        "48039": "Brazoria",
        "48041": "Brazos",
        "48043": "Brewster",
        "48045": "Briscoe",
        "48047": "Brooks",
        "48049": "Brown",
        "48051": "Burleson",
        "48053": "Burnet",
        "48055": "Caldwell",
        "48057": "Calhoun",
        "48059": "Callahan",
        "48061": "Cameron",
        "48063": "Camp",
        "48065": "Carson",
        "48067": "Cass",
        "48069": "Castro",
        "48071": "Chambers",
        "48073": "Cherokee",
        "48075": "Childress",
        "48077": "Clay",
        "48079": "Cochran",
        "48081": "Coke",
        "48083": "Coleman",
        "48085": "Collin",
        "48087": "Collingsworth",
        "48089": "Colorado",
        "48091": "Comal",
        "48093": "Comanche",
        "48095": "Concho",
        "48097": "Cooke",
        "48099": "Coryell",
        "48101": "Cottle",
        "48103": "Crane",
        "48105": "Crockett",
        "48107": "Crosby",
        "48109": "Culberson",
        "48111": "Dallam",
        "48113": "Dallas",
        "48115": "Dawson",
        "48117": "Deaf Smith",
        "48119": "Delta",
        "48121": "Denton",
        "48123": "DeWitt",
        "48125": "Dickens",
        "48127": "Dimmit",
        "48129": "Donley",
        "48131": "Duval",
        "48133": "Eastland",
        "48135": "Ector",
        "48137": "Edwards",
        "48139": "Ellis",
        "48141": "El Paso",
        "48143": "Erath",
        "48145": "Falls",
        "48147": "Fannin",
        "48149": "Fayette",
        "48151": "Fisher",
        "48153": "Floyd",
        "48155": "Foard",
        "48157": "Fort Bend",
        "48159": "Franklin",
        "48161": "Freestone",
        "48163": "Frio",
        "48165": "Gaines",
        "48167": "Galveston",
        "48169": "Garza",
        "48171": "Gillespie",
        "48173": "Glasscock",
        "48175": "Goliad",
        "48177": "Gonzales",
        "48179": "Gray",
        "48181": "Grayson",
        "48183": "Gregg",
        "48185": "Grimes",
        "48187": "Guadalupe",
        "48189": "Hale",
        "48191": "Hall",
        "48193": "Hamilton",
        "48195": "Hansford",
        "48197": "Hardeman",
        "48199": "Hardin",
        "48201": "Harris",
        "48203": "Harrison",
        "48205": "Hartley",
        "48207": "Haskell",
        "48209": "Hays",
        "48211": "Hemphill",
        "48213": "Henderson",
        "48215": "Hidalgo",
        "48217": "Hill",
        "48219": "Hockley",
        "48221": "Hood",
        "48223": "Hopkins",
        "48225": "Houston",
        "48227": "Howard",
        "48229": "Hudspeth",
        "48231": "Hunt",
        "48233": "Hutchinson",
        "48235": "Irion",
        "48237": "Jack",
        "48239": "Jackson",
        "48241": "Jasper",
        "48243": "Jeff Davis",
        "48245": "Jefferson",
        "48247": "Jim Hogg",
        "48249": "Jim Wells",
        "48251": "Johnson",
        "48253": "Jones",
        "48255": "Karnes",
        "48257": "Kaufman",
        "48259": "Kendall",
        "48261": "Kenedy",
        "48263": "Kent",
        "48265": "Kerr",
        "48267": "Kimble",
        "48269": "King",
        "48271": "Kinney",
        "48273": "Kleberg",
        "48275": "Knox",
        "48277": "Lamar",
        "48279": "Lamb",
        "48281": "Lampasas",
        "48283": "La Salle",
        "48285": "Lavaca",
        "48287": "Lee",
        "48289": "Leon",
        "48291": "Liberty",
        "48293": "Limestone",
        "48295": "Lipscomb",
        "48297": "Live Oak",
        "48299": "Llano",
        "48301": "Loving",
        "48303": "Lubbock",
        "48305": "Lynn",
        "48307": "McCulloch",
        "48309": "McLennan",
        "48311": "McMullen",
        "48313": "Madison",
        "48315": "Marion",
        "48317": "Martin",
        "48319": "Mason",
        "48321": "Matagorda",
        "48323": "Maverick",
        "48325": "Medina",
        "48327": "Menard",
        "48329": "Midland",
        "48331": "Milam",
        "48333": "Mills",
        "48335": "Mitchell",
        "48337": "Montague",
        "48339": "Montgomery",
        "48341": "Moore",
        "48343": "Morris",
        "48345": "Motley",
        "48347": "Nacogdoches",
        "48349": "Navarro",
        "48351": "Newton",
        "48353": "Nolan",
        "48355": "Nueces",
        "48357": "Ochiltree",
        "48359": "Oldham",
        "48361": "Orange",
        "48363": "Palo Pinto",
        "48365": "Panola",
        "48367": "Parker",
        "48369": "Parmer",
        "48371": "Pecos",
        "48373": "Polk",
        "48375": "Potter",
        "48377": "Presidio",
        "48379": "Rains",
        "48381": "Randall",
        "48383": "Reagan",
        "48385": "Real",
        "48387": "Red River",
        "48389": "Reeves",
        "48391": "Refugio",
        "48393": "Roberts",
        "48395": "Robertson",
        "48397": "Rockwall",
        "48399": "Runnels",
        "48401": "Rusk",
        "48403": "Sabine",
        "48405": "San Augustine",
        "48407": "San Jacinto",
        "48409": "San Patricio",
        "48411": "San Saba",
        "48413": "Schleicher",
        "48415": "Scurry",
        "48417": "Shackelford",
        "48419": "Shelby",
        "48421": "Sherman",
        "48423": "Smith",
        "48425": "Somervell",
        "48427": "Starr",
        "48429": "Stephens",
        "48431": "Sterling",
        "48433": "Stonewall",
        "48435": "Sutton",
        "48437": "Swisher",
        "48439": "Tarrant",
        "48441": "Taylor",
        "48443": "Terrell",
        "48445": "Terry",
        "48447": "Throckmorton",
        "48449": "Titus",
        "48451": "Tom Green",
        "48453": "Travis",
        "48455": "Trinity",
        "48457": "Tyler",
        "48459": "Upshur",
        "48461": "Upton",
        "48463": "Uvalde",
        "48465": "Val Verde",
        "48467": "Van Zandt",
        "48469": "Victoria",
        "48471": "Walker",
        "48473": "Waller",
        "48475": "Ward",
        "48477": "Washington",
        "48479": "Webb",
        "48481": "Wharton",
        "48483": "Wheeler",
        "48485": "Wichita",
        "48487": "Wilbarger",
        "48489": "Willacy",
        "48491": "Williamson",
        "48493": "Wilson",
        "48495": "Winkler",
        "48497": "Wise",
        "48499": "Wood",
        "48501": "Yoakum",
        "48503": "Young",
        "48505": "Zapata",
        "48507": "Zavala",
    }

    # Invert the map: County name => FIPS code
    COUNTY_TO_FIPS = {v: k for k, v in FIPS_MAP.items()}

    results = []
    for name in county_names:
        # Return FIPS code if county is found, else None
        results.append(COUNTY_TO_FIPS.get(name, None))
    return results
