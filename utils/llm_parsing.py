from typing import Any


def parse_dict_from_llm_bullet_points(llm_response: str) -> dict[str, Any]:
    """
    Parse a dictionary of bullet points from a response from the Language Learning Model.

    :param llm_response: The response from the LLM that follows the pattern of KEY = VALUE. If multiple values then comma-separated.
    :return: A dictionary of bullet points keyed by the field name.
    """
    bullet_points = {}
    for line in llm_response.split('\n'):
        try:
            key, value = line.split(' = ')
        except ValueError:
            # This happens when the line is the LLM bullshitting about (explaining, apologising etc.)
            continue
        key = key.lower()
        if value.upper() == "NONE":
            bullet_points[key] = None
            continue
        comma_separated = value.split(',')
        if len(comma_separated) == 1:
            bullet_points[key] = value
        else:
            bullet_points[key] = comma_separated
    return bullet_points
