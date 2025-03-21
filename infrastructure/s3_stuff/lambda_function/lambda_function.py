import json
import boto3
import time
import random
import string

def lambda_handler(event, context):
    print('Received S3 event:', json.dumps(event, indent=2))
    transcribe_client = boto3.client("transcribe")
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        print(f'New object created: {object_key} in bucket: {bucket_name}')
        # Job name should be bucket_name + object_key + current date
        job_name = f'{bucket_name}-{object_key}-{time.strftime("%Y%m%d-%H%M%S")}'
        file_uri = f's3://{bucket_name}/{object_key}'
        transcription_object =  transcribe_file(job_name, file_uri, transcribe_client)
        print(transcription_object)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed S3 event')    
    }


def transcribe_file(job_name, file_uri, transcribe_client):
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": file_uri},
        MediaFormat="wav",
        LanguageCode="en-US",
    )

    # Sleep for a bit to let the job start processing.
    time.sleep(5)

    # Check the status of the job.
    job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]
    print(f"Job {job_name} is {job_status}.")
