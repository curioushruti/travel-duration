from enum import Enum
import os
import time
import requests
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import ToolException, StructuredTool


class DistanceMatrixAPI(BaseModel):
    """Find the duration to travel between two locations by a given mode of transport."""

    origin: str = Field(..., description="Origin location address")
    destination: str = Field(..., description="Destination location address")
    mode: str = Field(
        ...,
        description="Mode of transport - must be one of 'driving', 'walking', 'bicycling', 'transit'",
    )  # defaults to driving


class mapsMode(Enum):
    DRIVING = "driving"
    WALKING = "walking"
    BICYCLING = "bicycling"
    TRANSIT = "transit"


def call_distance_matrix_api(
    origin: str,
    destination: str,
    mode: str,
) -> str:
    """Sample output from API:
    {'destination_addresses': ['Golden Gate Bridge, Golden Gate Brg, San Francisco, CA, USA'], 'origin_addresses': ['Redwood City, CA, USA'], 'rows': [{'elements': [{'distance': {'text': '49.2 km', 'value': 49159}, 'duration': {'text': '47 mins', 'value': 2792}, 'duration_in_traffic': {'text': '54 mins', 'value': 3218}, 'status': 'OK'}]}], 'status': 'OK'}"""

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # Check if the mode is valid
    if mode not in (item.value for item in mapsMode):
        raise ToolException(
            f"Invalid travel mode: {mode}. Please choose from: driving, walking, bicycling, transit."
        )

    params = {
        "origins": [origin],
        "destinations": [destination],
        "key": os.getenv("GOOGLE_MAPS_API_KEY"),
        "departure_time": int(
            time.time()
        ),  # departure time is required to get the current traffic information
        "mode": mode,
    }

    response = requests.get(url, params)

    if response.status_code == 200:
        duration = response.json()["rows"][0]["elements"][0]["duration"]["text"]
        if mode == mapsMode.DRIVING.value:
            duration = response.json()["rows"][0]["elements"][0]["duration_in_traffic"][
                "text"
            ]
        return duration
    else:
        raise ToolException(
            f"Unable to fetch data from Google Distance Matrix API, status: {response.status_code}. Try again later."
        )


def _handle_error(error: ToolException) -> str:
    return f"The following errors occurred during tool execution: `{error.args[0]}`"


distance_matrix_api = StructuredTool.from_function(
    func=call_distance_matrix_api,
    name="distance_matrix_api",
    args_schema=DistanceMatrixAPI,
    return_direct=True,
    handle_tool_errors=_handle_error,
)
