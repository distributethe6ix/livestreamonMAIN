import json

def lambda_handler(event, context):
    print('Received S3 event:', json.dumps(event, indent=2))
    
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        print(f'New object created: {object_key} in bucket: {bucket_name}')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed S3 event')
    }
