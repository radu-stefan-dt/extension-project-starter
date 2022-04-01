import yaml
import base64
from utils import Dynatrace, run_command


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
    
    dt.make_request(dt.CREDENTIALS_API, "POST", {
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
    api_token = config["api_token"]
    dt = Dynatrace(tenant_url, api_token)

    # Generate certificates
    generate()

    # Upload certificate to Dynatrace
    upload()