import asyncio
import json
import logging
import os
import polling
import requests
import ssl
from arcgis.gis import GIS
from dotenv import load_dotenv
from websockets.asyncio.client import connect

# Configuration
load_dotenv()
username = os.getenv("ARCGIS_USERNAME")
password = os.getenv("ARCGIS_PASSWORD")
portal_url = os.getenv("ARCGIS_PORTAL_URL")
workflow_server_url = os.getenv("WORKFLOW_SERVER_URL")
workflow_id = os.getenv("WORKFLOW_ID")

use_websockets = True          # Uses Polling when set to False.
polling_timeout = 300          # 5 minutes
polling_step = 1
verify_cert = False            # Warning: It is a securtity risk to set this to False.
log_filename = "Log_File.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='a'                # Append mode to keep existing logs and add new lines
)

async def run_vertigis_workflow(esri_token):
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
    if (vertigis_token is None):
        logging.info("Failed to retrieve VertiGIS Workflow Access Token from " + auth_token_run_url)
    else:
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
    def get_outputs(results):
        if results:
            job_quit_artifact = next((artifact for artifact in results if artifact.get("$type") == "JobQuit"), None)
            if job_quit_artifact:
                job_result_artifact = next((artifact for artifact in results if artifact.get("$type") == "JobResult"), None)
                if job_result_artifact:
                    return job_result_artifact.get("outputs")
        return None
    def wait_for_job_result_polling():
        def get_polling_outputs():
            data = requests.get(artifacts_url, params=params, headers=headers, verify=verify_cert).json()
            results = data.get("results", [])
            return get_outputs(results)
        outputs = polling.poll(
            get_polling_outputs,
            check_success=lambda v: v is not None,
            step=polling_step,
            timeout=polling_timeout
        )
        return outputs
    async def wait_for_job_result_websocket():
        # If 'https', this will intentionally result is 'wss' 
        websocket_artifacts_url = artifacts_url.replace("http",  "ws")
        artifacts_service_url = f"{websocket_artifacts_url}?ticket={ticket}"
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        async with connect(artifacts_service_url, ssl=True if verify_cert == True else ssl_context) as websocket:
            message = await websocket.recv()
            data = json.loads(message)
            results = data.get("results", [])
            return get_outputs(results)
    outputs = None
    if (use_websockets):
        outputs = await wait_for_job_result_websocket()
    else:
        outputs = wait_for_job_result_polling()
    logging.info(f"VertiGIS Workflow Outputs: {outputs}")
    print(outputs)


async def main():
    global username
    global password
    global portal_url

    if (password == ""):
        password = None

    if (portal_url == ""):
        portal_url = None

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
            await run_vertigis_workflow(esri_token)
        except Exception as e:
            logging.error(f"Error running VertiGIS Workflow: {e}")
            print(f"Error running VertiGIS Workflow: {e}")

    print(f"\nLogs are available at: {log_filename}")
    logging.info("\n\n\n=========================================================================================\n\n")

if __name__ == "__main__":
    asyncio.run(main()) 