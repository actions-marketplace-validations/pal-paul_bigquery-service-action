import datetime
import json
import os
import uuid
from google.cloud import bigquery
from dotenv import load_dotenv

def create_table(project_id, dataset_id, table_id):
    client = bigquery.Client()
    table_id = f"{project_id}.{dataset_id}.{table_id}"
    schema = [
        bigquery.SchemaField("job_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("job_date", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("job_status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("job_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("job_title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("job_message", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("job_stat", "STRING"),
        bigquery.SchemaField("git_workflow", "STRING"),
        bigquery.SchemaField("git_run_id", "STRING"),
        bigquery.SchemaField("git_job", "STRING"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table)  # Make an API request.
    print(
        "Created table {}.{}.{}".format(table.project, table.dataset_id, table.table_id)
    )

def table_insert_rows(payload, project_id, dataset_id, table_id):  
    client = bigquery.Client(project=project_id)
    is_table_exists = client.dataset(dataset_id).table(table_id).exists()

    if is_table_exists==False:
        create_table(project_id, dataset_id, table_id)

    rows_to_insert = payload
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))

def construct_payload(inputs):
    """
    Creates a message payload which can be sent to Slack.
    """

    # derived from workflow environment
    git_workflow = os.getenv('GITHUB_WORKFLOW')
    git_repo = os.getenv('GITHUB_REPOSITORY')
    git_branch = os.getenv('GITHUB_REF')
    git_commit_sha = os.getenv('GITHUB_SHA')[:7]
    git_run_id = os.getenv('GITHUB_RUN_ID')
    git_job = os.getenv('GITHUB_JOB')

    # derived from action inputs
    job_status = inputs['job_status']
    job_name = inputs['job_name']
    job_title = inputs['job_title']
    job_message = inputs['job_message']
    job_stat = inputs['job_stat']

    payload = [{
        u"job_id": uuid.uuid4(), 
        u"job_date": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 
        u"job_name": job_name, 
        u"job_title": job_title,
        u"job_message": job_message, 
        u"job_stat": job_stat,
        u"git_workflow": git_workflow, 
        u"git_run_id": git_run_id,
        u"git_job": git_job,
    }]

    return json.dumps(payload)

def main(testing=False):
    """
    Main function for the app.
    """

    inputs = {
        'job_status': os.getenv('INPUT_JOB_STATUS'),
        'job_name': os.getenv('INPUT_JOB_NAME'),
        'job_title': os.getenv('INPUT_JOB_TITLE'),
        'job_message': os.getenv('INPUT_JOB_MESSAGE'),
        'job_stat': os.getenv('INPUT_JOB_STAT'),
        'project': os.getenv('INPUT_PROJECT'),
        'dataset': os.getenv('INPUT_DATASET'),
        'table': os.getenv('INPUT_TABLE'),
        'notify_when': os.getenv('INPUT_NOTIFY_WHEN'),
    }

    payload = construct_payload(inputs)
    if inputs['job_status'] in inputs['notify_when'] and not testing:
        table_insert_rows(payload, inputs['project'], inputs['dataset'], inputs['table'])


if __name__ == '__main__':
    load_dotenv()
    main()