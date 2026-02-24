
import boto3
from CloudProvider import CloudProvider

class AwsScanner(CloudProvider):
    def __init__(self):
        super().__init__("AWS")

    def connect(self,arn):
        sts=boto3.client('sts')
        response=sts.assume_role(
            RoleArn=arn,
            RoleSessionName='ScannerSession'
        )
        credentials=response['Credentials']
        return credentials
        
    
    def scan(self,credentials):
        

        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )

        inventario = {
            'users': [],
            'groups': [],
            'roles': [],
            'buckets': [],
            'instances': []
        }

        iam=session.client('iam')
        users=iam.list_users()
        for user in users['Users']:
            inventario['users'].append(user['UserName'])
        groups=iam.list_groups()
        for group in groups['Groups']:
            inventario['groups'].append(group['GroupName'])
        roles=iam.list_roles()
        for role in roles['Roles']:
            inventario ['roles'].append(role['RoleName'])
              

        s3=session.client('s3')
        buckets = s3.list_buckets()
        for bucket in buckets['Buckets']:
            inventario['buckets'].append(bucket['Name'])
        
        ec2=session.client('ec2', region_name='us-east-1')
        instances=ec2.describe_instances()

        for reserva in instances['Reservations']:
            for instance in reserva['Instances']:
                inventario['instances'].append({
                    'InstanceId': instance['InstanceId'],
                    'State': instance['State']['Name']
                })


        return inventario



                   

