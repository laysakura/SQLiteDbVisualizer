import json

def output_dbinfo_json(dbinfo, json_path, json_encoding):
    with open(json_path, "w") as f_json:
        json_str = json.dumps(dbinfo, indent=2)
        f_json.write(json_str.encode(json_encoding))

