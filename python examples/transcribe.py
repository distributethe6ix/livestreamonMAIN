import time
import boto3

def upload_to_s3(file_path, bucket_name):
    s3 = boto3.client('s3')
    try:
        # split on '\' for windows and '/' for linux
        if '\\' in file_path:
            file_name = file_path.split('\\')[-1]
        else:
            file_name = file_path.split('/')[-1]
        s3.upload_file(file_path, bucket_name, file_name)
        object_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
        return object_url
    except FileNotFoundError:
        print("The file was not found")
        return None
    except NoCredentialsError:
        print("Credentials not available")
        return None

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
                return job ["TranscriptFileUri"]
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)


def main():
    file_path = input("Enter the file path: ")
    bucket_name = input("Enter the S3 bucket name: ")
    object_url = upload_to_s3(file_path, bucket_name)
    if object_url:
        print(f"File uploaded successfully. Accessible at: {object_url}")
    else:
        print("File upload failed.")
    transcribe_client = boto3.client("transcribe")
    transcribe_file_summarize = transcribe_file("liveonmain1", object_url, transcribe_client)
    prompt = "You are an transcript analyst. Please summarize this transcript with key details."
    object_name = transcribe_file_summarize.split('/')[-1]
    result = summarize_transcript_with_bedrock(bucket_name, object_name, prompt)

def summarize_transcript_with_bedrock(bucket_name, object_name, prompt):
    # Assuming you have the AWS Bedrock client set up
    bedrock = boto3.client("bedrock-runtime", region_name="ca-central-1")
    s3 = boto3.client('s3')

    #Get s3 object
    #object_name = object_url.split('/')[-1]
    response = s3.get_object(Bucket=bucket_name, Key=object_name)
    transcript_content = response['Body'].read().decode("utf-8")


    
    payload = {
        "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
        "contentType": "application/json",
        "accept": "application/json",
        "body": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "top_k": 250,
            "top_p": 0.999,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "source": {
                                "data": transcript_content
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
    }
    
    # Convert the payload to bytes
    body_bytes = json.dumps(payload['body']).encode('utf-8')
    
    # Invoke the model
    response = bedrock.invoke_model(
        body=body_bytes,
        contentType=payload['contentType'],
        accept=payload['accept'],
        modelId=payload['modelId']
    )
    
    # Process the response
    response_body = json.loads(response['body'].read())
    result = response_body['content'][0]['text']
    
    # If you need the full response, make sure only the response_body is returned.
    return result

if __name__ == "__main__":
    main()

