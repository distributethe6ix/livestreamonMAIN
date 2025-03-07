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
        job_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
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

    max_tries = 60
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]
        if job_status in ["COMPLETED", "FAILED"]:
            print(f"Job {job_name} is {job_status}.")
            if job_status == "COMPLETED":
                print(
                    f"Download the transcript from\n"
                    f"\t{job['TranscriptionJob']['Transcript']['TranscriptFileUri']}."
                )

                return job['TranscriptionJob']['Transcript']['TranscriptFileUri']
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)
