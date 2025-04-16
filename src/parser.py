import json
import re

def extract_entries(input_string):
    """
    Extracts and parses multiple JSON objects from a given string.

    Args:
        input_string (str): A string containing multiple JSON objects.

    Returns:
        list: A list of dictionaries representing the parsed JSON objects.
    """
    try:
        entries = []
        stack = []
        json_objects = []
        current_object = ""

        # Scan the input string character by character
        for char in input_string:
            if char == "{":
                stack.append(char)
            if char == "}":
                if stack:
                    stack.pop()

            # Append characters to current JSON object
            current_object += char

            # If stack is empty, we have a complete JSON object
            if not stack and current_object.strip():
                json_objects.append(current_object.strip())
                current_object = ""

        # Parse each detected JSON object
        for obj in json_objects:
            try:
                parsed_json = json.loads(obj)
                if "spd-entry" in parsed_json or "sad-entry" in parsed_json:
                    entries.append(parsed_json)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON object due to error: {e}")

        return entries

    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

