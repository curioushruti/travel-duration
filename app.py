############################
# To run this app:         #
# streamlit run app.py     #
############################

from typing import Tuple
import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from tools import (
    DistanceMatrixAPI,
    distance_matrix_api,
    call_distance_matrix_api,
)


def process_request(request: str) -> Tuple[str, DistanceMatrixAPI | None]:
    model = ChatAnthropic(model="claude-3-haiku-20240307")
    sys_prompt = """\
You are a helpful travel assistant. Your goal is to provide the user with latest information on travel duration between two locations of their choice with a mode of their choice. Assume the user is trying to depart right now. You don't have latest traffic information but you can invoke tools that will provide you travel duration between two locations. If the user's request is something other than a request for travel duration, let the user know you cannot help them with that and your scope is limited to helping them with travel duration."""
    system_message = SystemMessage(content=sys_prompt)
    user_req = HumanMessage(
        content="The user's request is: \n"
        + request
        + "Valid modes of transport include: walking, driving, transit, bicycling. If an invalid mode of transport is provided, let the user know that their desired mode of transport is unsupported and do not invoke the tool. If the user did not specify a mode of transport, assume they are driving. If an ambigious location (origin or destination) is specified by the user (e.g. Walgreens, since there are many Walgreens to choose from), use your own knowledge to assume the closest location to the other non-ambigous location specified in the user's request and provide an address in the tool invocation. If you cannot find a location, ask the user for more input by providing them some options. Do not invoke the tool with ambigious location like 'Safeway'."
    )

    # provide tools to the model
    tools = [distance_matrix_api]
    model = model.bind_tools(tools)

    response = model.invoke([system_message, user_req])

    # handle cases for when the user's request is not a request for travel duration
    if isinstance(response.content, str):
        return response.content, None

    for content in response.content:
        if content["type"] == "tool_use":
            json_response = content
            break
    tool_name = json_response["name"]

    if tool_name == "distance_matrix_api":
        tool_args = json_response["input"]
        api_input = DistanceMatrixAPI(**tool_args)
        try:
            duration = call_distance_matrix_api(
                api_input.origin,
                api_input.destination,
                api_input.mode if api_input.mode else "driving",
            )
            return duration, api_input
        except Exception as e:
            return f"Error: {e}"
    else:
        return "We've hit a snag. Please try again.", None


def format_response(
    duration: str, user_request: str, api_input: DistanceMatrixAPI
) -> str:
    model = ChatAnthropic(model="claude-3-haiku-20240307")
    sys_prompt = """\
You are a helpful travel assistant used to provide the user with latest information on travel duration between two locations. The travel duration is calculated by a separate tool whose results needs to be shared with the user. The user does not know about the tool, present the response as your own. Your goal is to format a response that will be displayed to the user so avoid any preface and get to the point."""
    system_message = SystemMessage(content=sys_prompt)
    user_message = HumanMessage(
        content=f"""\
Here is what the user wanted: {user_request}.
The duration calculated by the tool is: {duration}. The tool used mode of transport as: {api_input.mode}, origin as: {api_input.origin}, and destination as: {api_input.origin} to make this calculation. For driving, it also considers traffic conditions.
Here are your instructions for the task: 
1. If the origin or destination the tool used for calculating duration is different from the user's request, let the user know the nearest location was chosen.
2. Consider providing the exact origin ({api_input.origin}) and destination ({api_input.destination}) used for the calculation to the user for their reference.
3. Assess the request to see if you have information on their mode of transport, if not then assume they are driving. Do not assume this if they've mentioned how they intend to travel. 
4. If applicable, let the user know your assumption of the mode of transport. 
5. Provide the user with the duration calculated by the tool.
"""
    )

    response = model.invoke([system_message, user_message])

    return response.content


def main():
    # load environment variables from .env file (API keys are stored here)
    load_dotenv()

    st.title("Travel Duration Calculator")

    user_input = st.text_input("Where are you off to today?")

    if st.button("Go"):
        if user_input:
            try:
                (duration, api_input) = process_request(user_input)
                if api_input:
                    result = format_response(duration, user_input, api_input)
                    st.write(result)
                else:
                    st.write(duration)
            except Exception:
                st.write("An error occurred. Please try again.")
        else:
            st.write("Please enter a request.")
    return


if __name__ == "__main__":
    main()
