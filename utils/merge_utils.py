

def combine_data_contents(older: dict[str, dict], newer: dict[str, dict]) -> dict[str, dict]:
    """
    Combine two data_content dictionaries, giving precedence to newer data.
    If newer data leaves attributes empty that older data has, keep the older attributes.
    """
    combined = older.copy()
    for key, value in newer.items():
        if isinstance(value, dict):  # Assuming the value is a dict of attributes from Pydantic models
            # Only update attributes that are not empty in the newer data_content
            combined[key] = {attr: val if val is not None and val != "" else combined[key].get(attr)
                             for attr, val in value.items()}
        else:
            # If it's not a dict, assume it's a single value and should be overwritten if not empty
            combined[key] = value or combined.get(key)
    return combined