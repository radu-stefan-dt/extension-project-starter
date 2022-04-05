import yaml
import base64
from dtcli import signing
from datetime import datetime, timedelta, timezone
from utils import Dynatrace


def generate():
    print("Generating root and developer certificates...")
    cn = config.get('common_name', 'SomeDeveloper')
    o = config.get('org_name', 'SomeOrganization')
    ou = config.get('org_unit', 'SomeDepartment')

    root_subject = {"CN": cn, "O": f"{o}Root", "OU": ou }
    dev_subject = {"CN": cn, "O": f"{o}Developer", "OU": ou }

    expiration = datetime.now(tz=timezone.utc)+timedelta(days=config.get("days_valid", 1095))
    signing.generate_ca(
        ca_cert_file_path=config.get("ca_cert_path", "../certs/ca.pem"),
        ca_key_file_path=config.get("ca_key_path", "../certs/ca.key"),
        subject=root_subject,
        not_valid_after=expiration,
        passphrase=None
    )
    signing.generate_cert(
        ca_cert_file_path=config.get("ca_cert_path", "../certs/ca.pem"),
        ca_key_file_path=config.get("ca_key_path", "../certs/ca.key"),
        dev_cert_file_path=config.get("dev_cert_path", "../certs/dev.pem"),
        dev_key_file_path=config.get("dev_cert_path", "../certs/dev.key"),
        subject=dev_subject,
        dev_passphrase=None,
        ca_passphrase=None,
        not_valid_after=expiration,
    )
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