import boto3
from AwsScanner import AwsScanner
import json

def handler(event, context):
    try:
        arn=event['arn']
        awsScanner = AwsScanner()
        credentials = awsScanner.connect(arn)
        resultados = awsScanner.scan(credentials)
        return {
            'statusCode': 200,
            'body': json.dumps(resultados)
        }
    except Exception as e:
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }







if __name__ == "__main__":
  event = {
        'arn': 'arn:aws:iam::453195924129:role/testArn'
    }
  response = handler(event, None)
  print('body:', response['body'])
