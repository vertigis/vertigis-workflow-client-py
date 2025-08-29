# Run a VertiGIS Studio Workflow with Python

This script authenticates using your ArcGIS credentials and executes a VertiGIS Workflow.
It is particularly valuable for automating business logic on a recurring schedule with tools like cron jobs, windows task scheduler, or shell scripts.

## Requirements

- Python `3.12`\
    (The `arcgis` package will not work with Python `3.13`.)

## Storing Credentials

This script reads sensitive ArcGIS Credentials from an `.env` file located at the root of your project. Your `.env` should include the following values.

```
ARCGIS_USERNAME=<your_arcgis_username>
ARCGIS_PASSWORD=<your_arcgis_password>
ARCGIS_PORTAL_URL=https://<server>/portal
WORKFLOW_SERVER_URL=https://<server>/vertigisstudio/workflow/service
WORKFLOW_ID=<item_id_of_workflow_to_run>
```

## Setting Up Your Environment

All below commands are run from within the root of this repository.

### Create a virtual environment

`python3 -m venv .venv`

### Activate the virtual environment

`source .venv/bin/activate`

### Check python binaries are the correct path

```
# Should show you the the binary from the `.venv` folder
(venv) $ which pip
(venv) $ which python
```

### Install dependencies

`pip install requests && pip install polling && pip install dotenv && pip install arcgis`

### Run The Script

Once you have:
1) Created your `.env` file 
2) Created and activated the virtual directory

Run the script with `python3 run_vertigis_workflow.py`

### Deactive the virtual environment

`(venv) $ deactivate`

## Considerations
- This script makes use of VertiGIS RESTful API endpoints. You can view the endpoints and send sample requests at `https://<server>/vertigisstudio/workflow/service/specification`. 

- The server from the `WORKFLOW_SERVER_URL` in the .env file must expose an `/auth/token/run` endpoint, and this must be the same server hosting the `WORKFLOW_ID` in the .env file. If it is not, authentication will fail.

- The script prints the result of a `Set Workflow Output` Activity, where the `Name` field is `output`.