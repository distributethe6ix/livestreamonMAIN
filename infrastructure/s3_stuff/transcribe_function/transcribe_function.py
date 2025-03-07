
import json
import os
import boto3
import urllib.request

transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    print(f'Received event: {json.dumps(event, indent=2)}')
    
    transcription_job_name = event['detail']['TranscriptionJobName']
    print(f'Transcription job name: {transcription_job_name}')
    job = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)
    uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
    print(uri)
    content = urllib.request.urlopen(uri).read().decode('UTF-8')
    print(json.dumps(content))
    
    data =  json.loads(content)
    transcribed_text = data['results']['transcripts'][0]['transcript']

    
    prompt = "You are an transcript analyst. Please summarize this transcript with key details."
    result = summarize_transcript_with_bedrock(transcribed_text, prompt)
    print(result)

   # Upload the result to S3
    bucket_name = os.environ['BUCKET_NAME']
    file_name = f'summarized_{transcription_job_name}.txt'
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=result)
    print(f'Summary uploaded to s3://{bucket_name}/{file_name}')

    return {
        'statusCode': 200,
        'body': json.dumps('Transcription and summarization complete')
    }

def summarize_transcript_with_bedrock(transcript_data, prompt):
    # Assuming you have the AWS Bedrock client set up
    bedrock = boto3.client("bedrock-runtime", region_name="ca-central-1")

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
                            "text": transcript_data
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
