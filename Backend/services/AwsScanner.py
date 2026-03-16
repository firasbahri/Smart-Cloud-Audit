

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from .CloudProvider import CloudProvider
from fastapi import HTTPException

class AwsScanner(CloudProvider):
    session = None
    def __init__(self):
        super().__init__("AWS")

    def connect(self, arn):
        
        try:
            if not arn or not arn.startswith('arn:aws:iam::'):
                raise HTTPException(status_code=400, detail="Arn Invalido. Debe comenzar con 'arn:aws:iam::'")
            
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()    
            account_id = identity['Account']
       
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
            return account_id

          
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise HTTPException(status_code=403, detail=f"Acceso denegado al asumir rol: {arn}")
            elif error_code == 'InvalidClientTokenId':
                raise HTTPException(status_code=400, detail="Credenciales AWS inválidas")
            else:
                raise HTTPException(status_code=500, detail=f"Error al conectar con AWS: {e.response['Error']['Message']}")
        except NoCredentialsError:
            raise HTTPException(status_code=400, detail="No se encontraron credenciales AWS configuradas")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error inesperado al conectar: {str(e)}")

    def scan_users(self):

        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            iam = self.session.client('iam')
            print(iam.list_users()['Users'][0]['UserName'])
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
        """Escanea grupos IAM"""
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            iam = self.session.client('iam')
            groups = iam.list_groups()
            return groups['Groups']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar grupos IAM")
            raise Exception(f"Error al escanear grupos: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear grupos: {str(e)}")
    
    def scan_roles(self):
        """Escanea roles IAM"""
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            iam = self.session.client('iam')
            roles = iam.list_roles()
            return roles['Roles']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar roles IAM")
            raise Exception(f"Error al escanear roles: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear roles: {str(e)}")
    
    def scan_s3(self):
    
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            s3 = self.session.client('s3')
            buckets = s3.list_buckets()
            return buckets['Buckets']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar buckets S3")
            raise Exception(f"Error al escanear S3: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear S3: {str(e)}")
    
    def scan_ec2(self):
        """Escanea instancias EC2"""
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")
            
            ec2 = self.session.client('ec2', region_name='us-east-1')
            instances = ec2.describe_instances()
            return instances['Reservations']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar instancias EC2")
            raise Exception(f"Error al escanear EC2: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear EC2: {str(e)}")
    


    
    