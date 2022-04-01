import os
import json
import yaml
import requests


SCHEMAS_API = "api/v2/extensions/schemas"


def make_request(path: str) -> dict:
    url = f"{tenant_url}/{path}"
    return requests.get(url, headers=header).json()


def auth_header(token: str) -> dict:
    if token.startswith(".Env."):
        token = os.environ.get(token[5:], "")

    return {"Authorization": f"Api-Token {token}"}


def fetch_schemas(target_version: str):
    versions = make_request(SCHEMAS_API).get("versions", [])

    if target_version == "latest":
        version = versions[-1]
    else:
        matches = [v for v in versions if v.startswith(target_version)]
        if matches:
            version = matches[0]
        else:
            print(f"Target version {target_version} does not exist.")
            raise SystemExit
        
    print(f"Downloading schemas for version {version}")

    files = make_request(f"{SCHEMAS_API}/{version}").get("files", [])
    for file in files:
        schema = make_request(f"{SCHEMAS_API}/{version}/{file}")
        with open(file=f"{download_dir}/{file}", mode="w") as f:
            json.dump(schema, f, indent=2)

    print("Finished.")


if __name__ == "__main__":
    # Read config
    with open(file="config.yaml", mode="r") as f:
        config = yaml.load(f)

    # Set parameters
    target_version = str(config.get("schema_version", "latest"))
    download_dir = config.get("download_folder", "../schemas")
    tenant_url = config["tenant_url"]
    raw_token = config["api_token"]
    header = auth_header(raw_token)

    # Download all schemas of target version
    fetch_schemas(target_version)