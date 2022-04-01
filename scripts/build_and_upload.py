import os
import yaml
import glob
from utils import Dynatrace, run_command


def get_current_name_and_version():
    with open(file="../extension/extension.yaml", mode="r") as f:
        extension = yaml.safe_load(f)
    
    return extension.get("name"), extension.get("version")


def build():
    print(f"Building extension {name} version {version}...")
    run_command([
        "dt", "extension", "build",
        "--extension-directory", "../extension",
        "--target-directory", "../build",
        "--certificate", config.get("dev_cert_path", "../certs/dev.pem"),
        "--private-key", config.get("dev_key_path", "../certs/dev.key"),
        "--no-dev-passphrase"
    ])
    print("Completed.")


def clean_old_versions():
    version_data = dt.make_request(f"{dt.EXTENSIONS_API}/{name}")

    if version_data.get("totalCount", 0) >= 10:
        print("Removing oldest version to make room for new...")
        oldest = version_data.get("extensions", [{}])[0]
        dt.make_request(f"{dt.EXTENSIONS_API}/{name}/{oldest.get('version','')}","DELETE")


def upload():
    print("Uploading to Dynatrace...")
    file_list = glob.glob('../build/*')
    latest_file = max(file_list, key=os.path.getctime)
    run_command([
        "dt", "extension", "upload",
        "--tenant-url", tenant_url,
        "--api-token", api_token,
        latest_file
    ])


def activate():
    print("Activating latest version...")
    dt.make_request(
        f"{dt.EXTENSIONS_API}/{name}/environmentConfiguration",
        "PUT",
        {"version": version}
    )
    print("Finished")


if __name__ == "__main__":
    # Read config
    with open(file="config.yaml", mode="r") as f:
        config = yaml.safe_load(f)

    # Set parameters
    tenant_url = config["tenant_url"]
    api_token = config["api_token"]
    dt = Dynatrace(tenant_url, api_token)
    name, version = get_current_name_and_version()

    # Build extension
    build()

    # Check for previous versions
    clean_old_versions()

    # Upload to Dynatrace
    upload()

    # Activate the latest version
    activate()
