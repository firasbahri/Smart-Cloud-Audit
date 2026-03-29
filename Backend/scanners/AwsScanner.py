

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from .IScanner import IScanner
from Factories.awsFactory import AWSFactory
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class AwsScanner(IScanner):
    session = None
    def __init__(self):
        super().__init__("AWS")

    def get_resources(self):
        resources=["users","groups","roles","s3","ec2"]
        return resources

    def connect(self, arn):
        
        try:
            if not arn or not arn.startswith('arn:aws:iam::'):
                raise HTTPException(status_code=400, detail="Arn Invalido. Debe comenzar con 'arn:aws:iam::'")
            
            sts = boto3.client('sts')

       
            response = sts.assume_role(
                RoleArn=arn,
                RoleSessionName='ScannerSession'
            )
           
            credentials = response['Credentials']
            self.session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            client_st = self.session.client('sts')
            identity = client_st.get_caller_identity()
            account_id = identity['Account']
            return account_id

          
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                logger.error(f"Access denied when assuming role: {arn}")
                raise HTTPException(status_code=403, detail=f"Acceso denegado al asumir rol: {arn}")
            elif error_code == 'InvalidClientTokenId':
                logger.error(f"Invalid AWS credentials when connecting with ARN {arn}")
                raise HTTPException(status_code=400, detail="Credenciales AWS inválidas")
            else:
                logger.error(f"ClientError when connecting to AWS with ARN {arn}: {e.response['Error']['Message']}")
                raise HTTPException(status_code=500, detail=f"Error al conectar con AWS: {e.response['Error']['Message']}")
        except NoCredentialsError:
            raise HTTPException(status_code=400, detail="No se encontraron credenciales AWS configuradas")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error inesperado al conectar: {str(e)}")

    def scan_resource(self, resource):
        if resource == "users":
            users=self.scan_users()
            logger.info(f"Scanned users: {users}")
            return AWSFactory.create_users(users)
        elif resource == "groups":
            groups=self.scan_groups()
            return AWSFactory.create_groups(groups)
        elif resource == "roles":
            roles=self.scan_roles()
            return AWSFactory.create_roles(roles)
        elif resource == "s3":
            buckets=self.scan_s3()
            return AWSFactory.create_buckets(buckets)
        elif resource == "ec2":
            ec2_instances=self.scan_ec2()
            return AWSFactory.create_ec2(ec2_instances)
        else:
            logger.error(f"Resource type {resource} not supported for scanning")
            raise HTTPException(status_code=400, detail=f"Recurso {resource} no soportado para escanear")
            
        

    def scan_users(self):
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            iam = self.session.client('iam')
            users = iam.list_users()['Users']
            try:
                summary = iam.get_account_summary()['SummaryMap']
                
                root_user = {
                    'UserName': 'root',
                    'UserId': 'root',
                    'Arn': None,
                    'CreateDate': None,
                    'MfaActive': summary.get('AccountMFAEnabled', False),
                    'AccessKeysPresent': summary.get('AccountAccessKeysPresent', 0),
                }
                
                users.append(root_user)
                for u in users:
                    if u['UserName'] == 'root':
                        continue
                    try:
                        mfa=iam.list_mfa_devices(UserName=u['UserName'])['MFADevices']
                        u['Mfa_enabled'] = len(mfa) > 0

                    except ClientError:
                        u['Mfa_enabled'] = False
                    
                    try:
                        access_keys=iam.list_access_keys(UserName=u['UserName'])['AccessKeyMetadata']
                        u['AccessKeyMetadata'] = access_keys
                    except ClientError:
                        u['AccessKeyMetadata'] = []    

                    try:
                        policies = iam.list_attached_user_policies(UserName=u['UserName'])['AttachedPolicies']
                        u['AttachedManagedPolicies'] = policies
                    except ClientError:
                        u['AttachedManagedPolicies'] = []            
            except ClientError as e:
                # Si no hay permisos para obtener summary, continuar sin root
                if e.response['Error']['Code'] != 'AccessDenied':
                    raise
            
            return users
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar usuarios IAM")
            raise Exception(f"Error al escanear usuarios: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear usuarios: {str(e)}")
    
    def scan_groups(self):
      
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            iam = self.session.client('iam')
            groups = iam.list_groups()
            for g in groups['Groups']:
                try:
                    users = iam.get_group(GroupName=g['GroupName'])['Users']
                    g['Users'] = users
                except ClientError:
                    g['Users'] = []
                
                try:
                    policies = iam.list_attached_group_policies(GroupName=g['GroupName'])['AttachedPolicies']
                    g['AttachedManagedPolicies'] = policies
                except ClientError:
                    g['AttachedManagedPolicies'] = []
            return groups['Groups']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar grupos IAM")
            raise Exception(f"Error al escanear grupos: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear grupos: {str(e)}")
    
    def scan_roles(self):

        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            iam = self.session.client('iam')
            roles = iam.list_roles()
            for r in roles['Roles']:
                try:
                    policies = iam.list_attached_role_policies(RoleName=r['RoleName'])['AttachedPolicies']
                    r['AttachedManagedPolicies'] = policies
                except ClientError:
                    r['AttachedManagedPolicies'] = []

            return roles['Roles']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                logger.error(f"Access denied when listing IAM roles")
                raise PermissionError("Sin permisos para listar roles IAM")
            raise Exception(f"Error al escanear roles: {e.response['Error']['Message']}")
        except Exception as e:
            logger.error(f"Unexpected error when scanning IAM roles: {str(e)}")
            raise Exception(f"Error inesperado al escanear roles: {str(e)}")
    
    def scan_s3(self):
    
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            s3 = self.session.client('s3')
            buckets = s3.list_buckets()
            for b in buckets['Buckets']:
                b['name'] = b['Name']
                b['CreationDate'] = b['CreationDate'].isoformat() 
                try:
                    public_access = s3.get_public_access_block(Bucket=b['Name'])
                    b['PublicAccess'] = public_access.get('PublicAccessBlockConfiguration',None)
                except ClientError:
                    b['PublicAccess'] = None
                try:
                    versioning = s3.get_bucket_versioning(Bucket=b['Name'])
                    b['Versioning'] = versioning.get('Status','Disabled')
                except ClientError:
                    b['Versioning'] = 'Disabled'

                try:
                    encryption = s3.get_bucket_encryption(Bucket=b['Name'])
                    b['Encryption'] = True
                except ClientError:
                    b['Encryption'] = False

                try:
                    policies = s3.get_bucket_policy(Bucket=b['Name'])
                    b['Policies'] = policies.get('Policy', None)
                except ClientError:
                    b['Policies'] = None

                try:
                    location = s3.get_bucket_location(Bucket=b['Name'])
                    b['Region'] = location.get('LocationConstraint')
                except ClientError:
                    b['Region'] = 'Unknown'


            return buckets['Buckets']

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                logger.error(f"Access denied when listing S3 buckets")
                raise PermissionError("Sin permisos para listar buckets S3")
            raise Exception(f"Error al escanear S3: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear S3: {str(e)}")
    
    def scan_ec2(self):
        
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            ec2 = self.session.client('ec2', region_name='us-east-1')
            instances = ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    try:
                        volumes = ec2.describe_volumes(Filters=[{'Name': 'attachment.instance-id', 'Values': [instance['InstanceId']]}])
                        list_volumes = []
                        for v in volumes['Volumes']:
                            list_volumes.append({
                                "VolumeId": v['VolumeId'],
                                "encryption": v['Encrypted']
                            })
                        instance['volumes'] = list_volumes
                    except ClientError:
                        instance['volumes'] = None

            return instances['Reservations']
    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar instancias EC2")
            raise Exception(f"Error al escanear EC2: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear EC2: {str(e)}")
    


    
    