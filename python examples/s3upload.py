import boto3
import base64
import json
from botocore.exceptions import NoCredentialsError

## This script uploads an image to an S3 bucket and then uses the Bedrock API to analyze the image.

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
    
def analyze_image_with_bedrock(bucket_name, object_name, prompt):
    # Assuming you have the AWS Bedrock client set up
    bedrock = boto3.client("bedrock-runtime", region_name="ca-central-1")
    s3 = boto3.client('s3')

    # Get s3 object
    response = s3.get_object(Bucket=bucket_name, Key=object_name)
    image_content = response['Body'].read()

    base64_encoded_image = base64.b64encode(image_content).decode('utf-8')

    
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
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_encoded_image
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
    
def main():
    file_path = input("Enter the file path: ")
    bucket_name = input("Enter the S3 bucket name: ")
    object_url = upload_to_s3(file_path, bucket_name)
    if object_url:
        print(f"File uploaded successfully. Accessible at: {object_url}")
    else:
        print("File upload failed.")

    prompt = "You are an image analyst. Please tell us if the provided photo contains sensitive information in the <result> tag with YES or NO and why in the <reason> tag. Explanations and reasons are not required. ### Example ### <result>NO</result> <reason>No sensitive content detected.</reason>"
    object_name = object_url.split('/')[-1]
    result = analyze_image_with_bedrock(bucket_name, object_name, prompt)

    print(result)

if __name__ == "__main__":
    main()