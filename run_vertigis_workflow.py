import os
import sys
import time
import logging
import requests 
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


log_filename = "Log_File.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='a'  # Append mode to keep existing logs and add new lines
)

def run_vertigis_workflow(esriToken):
    # Generate vertigis token
    auth_token_run_url = workflow_url + "/auth/token/run"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "accessToken": esriToken,
        "portalUrl": portal_url,
    }
    response = requests.post(auth_token_run_url, headers=headers, json=payload, verify=False)
    logging.info(f"VertiGIS Auth Token Response: {response.status_code} - {response.text}")
    vertigisToken = response.json().get("token")
    headers["Authorization"] = f"Bearer {vertigisToken}"
   
    # Submit job
    job_run_url = workflow_url + "/job/run"
    payload = {
        "workflow": {
            "id": workflow_id
        },
        "inputs": {}
    }
    response = requests.post(job_run_url, headers=headers, json=payload, verify=False)
    ticket = response.json().get("ticket")
    logging.info(f"VertiGIS Submit Job Response: {response.status_code} - {response.text}")

    # Get job artifacts
    artifacts_url = workflow_url + "/job/artifacts"
    params = {
        "ticket": ticket
    }
    response = requests.get(artifacts_url, params=params, headers=headers, verify=False)
    tag = response.json().get("results")[0].get("tag")
    logging.info(f"VertiGIS Job Artifacts Response: {response.status_code} - {response.text}")

    # Get job result
    result_url = workflow_url + "/job/result"
    params = {
        "ticket": ticket,
        "tag": tag
    }
    response = requests.get(result_url, params=params, headers=headers, verify=False)
    output = response.json().get("output")
    logging.info(f"VertiGIS Job Results Response: {response.status_code} - {response.text}")
    
    # Workflow has finished executing, print workflow output.
    print(output)


def main():
    esriToken: None
    try:
        gis = GIS(portal_url, username, password, verify_cert=False)
        logging.info(f"Successfully logged in to GIS Portal as: {gis.users.me.username}")
        esriToken = gis._con.token
        logging.info(f"ArgGIS Token: {esriToken}")
    except Exception as e:
        logging.error(f"Error logging into GIS Portal: {e}")
        print(f"Error logging into GIS Portal: {e}")

    try:
        run_vertigis_workflow(esriToken)
    except Exception as e:
        logging.error(f"Error running VertiGIS Workflow: {e}")
        print(f"Error running VertiGIS Workflow: {e}")

    print(f"\nLogs are available at: {log_filename}")
    logging.info("\n\n\n=========================================================================================\n\n")


if __name__ == "__main__":
    main()