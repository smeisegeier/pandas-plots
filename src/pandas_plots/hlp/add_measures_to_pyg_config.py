import os
import json
import uuid


def add_measures_to_pyg_config(json_path: str, nodes: list[tuple[str, str]] = [("cnt_tum", "count(distinct z_tum_id)")], strict: bool = False) -> None:
    """
    Reads a pygwalker JSON config file, adds new measures from given nodes if not already present, and writes back to the file.

    Parameters
    ----------
    json_path : `str`
        The path to the pygwalker JSON config file.
    nodes : `list[tuple[str, str]]`, optional
        A list of tuples, where the first element in the tuple is the name of the measure and the second element is the SQL expression that defines the measure. Default is `[('cnt_tum', 'count(distinct z_tum_id)')]`.
    strict : `bool`, optional
        If True, raises an error if the file does not exist or if JSON parsing fails. If False, the function exits silently in such cases. Default is False.

    Returns
    -------
    None

    Example
    -------
    default: `add_measures_to_pyg_config('config.json', [('cnt_tum', 'count(distinct z_tum_id)')], strict=True)`
    
    usage: start pygwalker with empty config file but defined config path. make changes on the chart, save the config file. then run this function again - measures will be added
    """
    if not os.path.exists(json_path):
        if strict:
            raise FileNotFoundError(f"File not found: {json_path}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError:
        if strict:
            raise
        return

    for node in nodes:
        fid = uuid.uuid4().hex
        
        # * Define the measure
        new_json_node = {
            "analyticType": "measure",
            "fid": f"{fid}",
            "name": f"{node[0]}",
            "semanticType": "quantitative",
            "computed": True,
            "aggName": "expr",
            "expression": {
                "op": "expr",
                "as": f"{fid}",
                "params": [{"type": "sql", "value": f"{node[1]}"}]
            }
        }

        # * Get the measures list
        measures = config.get("config", [{}])[0].get("encodings", {}).get("measures", [])

        # * Ensure the measure is present
        if not any(measure.get("name") == node[0] for measure in measures):
            measures.append(new_json_node)

    # * Write the updated JSON back to the file
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)