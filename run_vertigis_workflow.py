import os
import sys
import time
import logging
import requests
import polling
from dotenv import load_dotenv
from arcgis.gis import GIS
from datetime import datetime

# Configuration
load_dotenv()
username = os.getenv("ARCGIS_USERNAME")
password = os.getenv("ARCGIS_PASSWORD")
portal_url = os.getenv("ARCGIS_PORTAL_URL")
workflow_url = os.getenv("WORKFLOW_URL")
workflow_id = os.getenv("WORKFLOW_ID")

polling_timeout = 300  # 5 minutes
polling_step = 1

verify_cert = True # Warning: It is a securtity risk to set this to False.

log_filename = "Log_File.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='a'  # Append mode to keep existing logs and add new lines
)

def run_vertigis_workflow(esri_token):
    # Generate vertigis token
    auth_token_run_url = workflow_url + "/auth/token/run"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "accessToken": esri_token,
        "portalUrl": portal_url,
    }
    vertigis_token = polling.poll(
        lambda: requests.post(auth_token_run_url, headers=headers, json=payload, verify=verify_cert).json().get("token"),
        check_success=lambda token: token is not None,
        step = polling_step,
        timeout = polling_timeout
    )
    logging.info("VertiGIS Token: " + vertigis_token)
    headers["Authorization"] = f"Bearer {vertigis_token}"
   
    # Submit job
    job_run_url = workflow_url + "/job/run"
    payload = {
        "workflow": {
            "id": workflow_id
        },
        "inputs": {}
    }
    ticket = polling.poll(
        lambda: requests.post(job_run_url, headers=headers, json=payload, verify=verify_cert).json().get("ticket"),
        check_success = lambda ticket: ticket is not None,
        step = polling_step,
        timeout = polling_timeout
    )
    logging.info("VertiGIS Ticket: " + ticket)

    # Get job artifacts
    artifacts_url = workflow_url + "/job/artifacts"
    params = {
        "ticket": ticket
    }
    def get_tag():
        data = requests.get(artifacts_url, params=params, headers=headers, verify=verify_cert).json()
        results = data.get("results", [])
        if results:
            return results[0].get("tag")
        return None
    tag = polling.poll(
        get_tag,
        check_success=lambda v: v is not None,
        step=polling_step,
        timeout=polling_timeout
    )
    logging.info("VertiGIS Job Artifacts Tag: " + tag)

    # Get job result
    result_url = workflow_url + "/job/result"
    params = {
        "ticket": ticket,
        "tag": tag
    }
    output = polling.poll(
        lambda: requests.get(result_url, params=params, headers=headers, verify=verify_cert).json().get("output"),
        check_success=lambda output: output is not None,
        step = polling_step,
        timeout = polling_timeout
    )
    logging.info("VertiGIS Output: " + output)
    print(output)


def main():
    esri_token: None
    try:
        gis = GIS(portal_url, username, password, verify_cert=verify_cert)
        logging.info(f"Successfully logged in to GIS Portal as: {gis.users.me.username}")
        esri_token = gis._con.token
        logging.info(f"ArgGIS Token: {esri_token}")
    except Exception as e:
        logging.error(f"Error logging into GIS Portal: {e}")
        print(f"Error logging into GIS Portal: {e}")

    try:
        run_vertigis_workflow(esri_token)
    except Exception as e:
        logging.error(f"Error running VertiGIS Workflow: {e}")
        print(f"Error running VertiGIS Workflow: {e}")

    print(f"\nLogs are available at: {log_filename}")
    logging.info("\n\n\n=========================================================================================\n\n")


if __name__ == "__main__":
    main()