import os
import logging
import requests
import polling
from dotenv import load_dotenv
from arcgis.gis import GIS

# Configuration
load_dotenv()
username = os.getenv("ARCGIS_USERNAME")
password = os.getenv("ARCGIS_PASSWORD")
portal_url = os.getenv("ARCGIS_PORTAL_URL")
workflow_server_url = os.getenv("WORKFLOW_SERVER_URL")
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
    # Generate Access Token
    auth_token_run_url = workflow_server_url + "/auth/token/run"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "accessToken": esri_token,
        "portalUrl": portal_url,
    }
    response = requests.post(auth_token_run_url, headers=headers, json=payload, verify=False)
    vertigis_token = response.json().get("token")
    logging.info("VertiGIS Workflow Access Token: " + vertigis_token)
    headers["Authorization"] = f"Bearer {vertigis_token}"
   
    # Submit Job
    job_run_url = workflow_server_url + "/job/run"
    payload = {
        "workflow": {
            "id": workflow_id
        },
        "inputs": {}
    }
    response = requests.post(job_run_url, headers=headers, json=payload, verify=False)
    ticket = response.json().get("ticket")
    logging.info("VertiGIS Workflow Job Ticket: " + ticket)

    # Get Job Artifacts
    artifacts_url = workflow_server_url + "/job/artifacts"
    params = {
        "ticket": ticket
    }
    def get_outputs():
        data = requests.get(artifacts_url, params=params, headers=headers, verify=verify_cert).json()
        results = data.get("results", [])
        if results:
            job_quit_artifact = next((artifact for artifact in results if artifact.get("$type") == "JobQuit"), None)
            if job_quit_artifact:
                job_result_artifact = next((artifact for artifact in results if artifact.get("$type") == "JobResult"), None)
                if job_result_artifact:
                    return job_result_artifact.get("outputs")
        return None
    outputs = polling.poll(
        get_outputs,
        check_success=lambda v: v is not None,
        step=polling_step,
        timeout=polling_timeout
    )
    logging.info("VertiGIS Workflow Outputs: " + outputs)
    print(outputs)


def main():
    esri_token = None
    try:
        gis = GIS(portal_url, username, password, verify_cert=verify_cert)
        logging.info(f"Successfully logged in to GIS Portal as: {gis.users.me.username}")
        esri_token = gis._con.token
        logging.info(f"ArgGIS Token: {esri_token}")
    except Exception as e:
        logging.error(f"Error logging into GIS Portal: {e}")
        print(f"Error logging into GIS Portal: {e}")

    if esri_token is not None:
        try:
            run_vertigis_workflow(esri_token)
        except Exception as e:
            logging.error(f"Error running VertiGIS Workflow: {e}")
            print(f"Error running VertiGIS Workflow: {e}")

    print(f"\nLogs are available at: {log_filename}")
    logging.info("\n\n\n=========================================================================================\n\n")


if __name__ == "__main__":
    main()