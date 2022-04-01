import os
import yaml
import base64
import requests
import subprocess


CREDENTIALS_API = "api/config/v1/credentials"


def make_request(path: str, method: str="GET", json: dict=None) -> dict:
    url = f"{tenant_url}/{path}"
    header = {'Authorization': f'Api-Token {api_token}'}
    resp = requests.request(
        url=url,
        method=method, 
        headers=header,
        json=json
    )
    if resp.status_code not in [200, 201, 204]:
        print("Could not complete request")
        print(resp.text)
        raise SystemExit

    return resp.json()


def get_token(raw: str) -> dict:
    if raw.startswith(".Env."):
        return os.environ.get(raw[5:], "")

    return raw


def run_command(command: list):
    cmd = ["powershell.exe"] if os.name == "nt" else []
    cmd.extend(command)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(proc.stdout.readline, b''):
        print(">>> "+line.decode().rstrip())


def generate():
    print("Generating root and developer certificates...")
    subject = (
        f"/CN={config.get('common_name', 'SomeDeveloper')}"
        f"/O={config.get('org_name', 'SomeOrganization')}"
        f"/OU={config.get('org_unit', 'SomeDepartment')}"
    )
    run_command([
        "dt", "extension", "gencerts",
        "--ca-cert", config.get("ca_cert_path", "../certs/ca.pem"),
        "--ca-key", config.get("ca_key_path", "../certs/ca.key"),
        "--dev-cert", config.get("dev_cert_path", "../certs/dev.pem"),
        "--dev-key", config.get("dev_key_path", "../certs/dev.key"),
        "--ca-subject", subject,
        "--days-valid", str(config.get('days_valid', 1095)),
        "--no-dev-passphrase", "--no-ca-passphrase", "--force"
    ])
    print("Done.")


def upload():
    print("Uploading certificate to Credentials Vault...")
    cert_file = config.get("ca_cert_path", "../certs/ca.pem")
    with open(file=cert_file, mode="r") as f:
        cert_text = f.read()
    certificate = base64.b64encode(cert_text.encode('ascii')).decode('ascii')
    password = base64.b64encode("password_not_supported".encode('ascii')).decode('ascii')
    
    make_request(CREDENTIALS_API, "POST", {
        "name": "Extension Developer Certificate",
        "description": (
            "A developer's certificate used for signing Extensions 2.0. "
            "This was automatically generated using a convenience script."
        ),
        "ownerAccessOnly": True,
        "scope": "EXTENSION",
        "type": "PUBLIC_CERTIFICATE",
        "certificate": certificate,
        "password": password,
        "certificateFormat": "PEM"
    })

    print("Finished.")


if __name__ == "__main__":
    # Read config
    with open(file="config.yaml", mode="r") as f:
        config = yaml.safe_load(f)

    # Set parameters
    tenant_url = config["tenant_url"]
    api_token = get_token(config["api_token"])

    # Generate certificates
    generate()

    # Upload certificate to Dynatrace
    upload()