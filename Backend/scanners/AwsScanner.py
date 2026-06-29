

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from .IScanner import IScanner
from Factories.awsFactory import AWSFactory
from fastapi import HTTPException
import logging
import json

logger = logging.getLogger(__name__)

class AwsScanner(IScanner):
    """Scanner concreto para AWS: usa boto3 (vía un rol asumido con STS) para leer IAM, EC2 y S3 de la cuenta del usuario."""
    session = None
    def __init__(self):
        super().__init__("AWS")

    def get_resources(self):
        """Tipos de recurso AWS soportados hoy. Si se añade otro servicio (RDS, Lambda...), hay que sumarlo aquí."""
        resources=["users","groups","roles","s3","ec2"]
        return resources

    def connect(self, arn):
        """Asume el rol IAM de solo lectura que el usuario configuró y abre una sesión de boto3 con esas credenciales temporales.

        Args:
            arn (str): ARN del rol a asumir, formato "arn:aws:iam::<id_cuenta>:role/<nombre>".

        Returns:
            str: account_id de la cuenta AWS conectada (sacado de sts.get_caller_identity()).

        Raises:
            HTTPException: 400 si el ARN no tiene el formato esperado o boto3 no encuentra credenciales locales,
                403 si el assume-role es denegado (rol mal configurado o trust policy incorrecta),
                500 para cualquier otro error de AWS no controlado.
        """

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
                aws_session_token=credentials['SessionToken'],
                region_name='us-east-1'
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

    def scan_resource(self, resource,regions):
        """Despacha el escaneo según el tipo de recurso pedido y devuelve los datos ya convertidos al modelo de dominio.

        El caso "ec2" es distinto a los demás: scan_ec2 además devuelve en qué regiones encontró algo, así que aquí
        se propaga esa segunda parte hacia arriba (a scanController) en vez de devolver solo la lista de instancias.

        Args:
            resource (str): uno de los valores de get_resources() ("users", "groups", "roles", "s3", "ec2").
            regions (list): regiones AWS a recorrer; solo se usa para "ec2" (los demás servicios son globales o
                se consultan vía un único endpoint).

        Returns:
            list: recursos ya convertidos a modelo de dominio. Para "ec2" devuelve una tupla
            (instancias, regiones_con_resultados) en vez de solo la lista.

        Raises:
            HTTPException: 400 si resource no es ninguno de los soportados.
        """
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
            ec2_instances , regions_founded=self.scan_ec2(regions)
            return AWSFactory.create_ec2(ec2_instances), regions_founded
        else:
            logger.error(f"Resource type {resource} not supported for scanning")
            raise HTTPException(status_code=400, detail=f"Recurso {resource} no soportado para escanear")



    def scan_users(self):
        """Lista los usuarios IAM de la cuenta y completa cada uno con MFA, claves de acceso, políticas inline y
        managed. Añade también un usuario "root" sintético con el estado de MFA de la cuenta, sacado de
        get_account_summary (root no aparece en list_users).

        Returns:
            list[dict]: usuarios en formato crudo de boto3, con los campos extra Mfa_enabled, AccessKeyMetadata,
            InlinePolicies y AttachedManagedPolicies añadidos a mano.

        Raises:
            PermissionError: si el rol no tiene permiso para listar usuarios IAM.
            Exception: cualquier otro fallo de la API de IAM.
        """
        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")

            iam = self.session.client('iam')
            users = iam.list_users()['Users']
            try:
                summary = iam.get_account_summary()['SummaryMap']
                mfa_enabled = summary.get('AccountMFAEnabled', False)
                logger.info(f"Account MFA enabled: {mfa_enabled}")
                root_user = {
                    'UserName': 'root',
                    'UserId': 'root',
                    'Arn': None,
                    'CreateDate': None,
                    'Mfa_enabled': bool(summary.get('AccountMFAEnabled', 0)),
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
                        u["InlinePolicies"] = []
                        inlinePolicies = iam.list_user_policies(UserName=u['UserName'])['PolicyNames']
                        logger.info(f"User {u['UserName']} has inline policies: {inlinePolicies}")
                        for policy_name in inlinePolicies:
                            policy_document = iam.get_user_policy(UserName=u['UserName'], PolicyName=policy_name)['PolicyDocument']
                            logger.info(f"Policy document for {policy_name}: {policy_document}")
                            u["InlinePolicies"].append({
                                "PolicyName": policy_name,
                                "PolicyDocument": policy_document
                            })
                    except ClientError:
                        u["InlinePolicies"] = []


                    try:
                        Managedpolicies = iam.list_attached_user_policies(UserName=u['UserName'])['AttachedPolicies']
                        u['AttachedManagedPolicies'] = Managedpolicies
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
        """Lista los grupos IAM y, para cada uno, sus miembros y sus políticas (inline y managed).

        Returns:
            list[dict]: grupos en formato crudo de boto3 con Users, InlinePolicies y AttachedManagedPolicies añadidos.

        Raises:
            PermissionError: sin permisos para listar grupos IAM.
            Exception: cualquier otro fallo de la API.
        """

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

                try :
                    inlinePolicies = iam.list_group_policies(GroupName=g['GroupName'])['PolicyNames']
                    g['InlinePolicies'] = []
                    for policy_name in inlinePolicies:
                        policy_document = iam.get_group_policy(GroupName=g['GroupName'], PolicyName=policy_name)['PolicyDocument']
                        logger.info(f"Policy document for group {g['GroupName']} and policy {policy_name}: {policy_document}")
                        g['InlinePolicies'].append({
                            "PolicyName": policy_name,
                            "PolicyDocument": policy_document
                        })

                except ClientError:
                    g['InlinePolicies'] = []
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
        """Lista los roles IAM con sus políticas adjuntas y, en TrustPolicy, quién puede asumir cada rol
        (clave para que IAM_Analyzer detecte roles privilegiados asumibles desde fuera de la cuenta).

        Returns:
            list[dict]: roles en formato crudo de boto3, con AttachedManagedPolicies, InlinePolicies y
            TrustPolicy añadidos.

        Raises:
            PermissionError: sin permisos para listar roles IAM.
            Exception: cualquier otro fallo de la API.
        """

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

                try:
                    inlinePolicies = iam.list_role_policies(RoleName=r['RoleName'])['PolicyNames']
                    r['InlinePolicies'] = []
                    for policy_name in inlinePolicies:
                        policy_document = iam.get_role_policy(RoleName=r['RoleName'], PolicyName=policy_name)['PolicyDocument']
                        logger.info(f"Policy document for role {r['RoleName']} and policy {policy_name}: {policy_document}")
                        r['InlinePolicies'].append({
                            "PolicyName": policy_name,
                            "PolicyDocument": policy_document
                        })
                except ClientError:
                    r['InlinePolicies'] = []

                r['TrustPolicy'] = r.get('AssumeRolePolicyDocument', {})

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
        """Lista los buckets S3 y, para cada uno, su configuración de acceso público, versionado, cifrado,
        política y región — cada una de esas llamadas puede fallar por permisos sin tirar todo el scan abajo,
        así que cada una tiene su propio valor por defecto si no se puede leer.

        Returns:
            list[dict]: buckets en formato crudo de boto3 con name, PublicAccess, Versioning, Encryption,
            Policies y Region añadidos.

        Raises:
            PermissionError: sin permisos para listar buckets S3.
            Exception: cualquier otro fallo de la API.
        """

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
                    policies_str=policies.get('Policy', None)
                    b['Policies'] = json.loads(policies_str) if policies_str else None
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

    def scan_ec2(self, regions):
        """Recorre las regiones indicadas (o las ~30 regiones de la cuenta si no se pasa ninguna) buscando
        instancias EC2, y para cada instancia encontrada añade sus volúmenes EBS y grupos de seguridad.

        Una región sin instancias se salta sin marcarse como encontrada — así regions_founded acaba siendo
        justo el subconjunto de regiones donde de verdad hay algo, útil para que la próxima vez no haga falta
        recorrer las 30 si la cuenta solo usa 2 o 3.

        Args:
            regions (list | None): regiones a escanear. Si es None o lista vacía, se autodetectan todas las
                regiones habilitadas de la cuenta vía describe_regions().

        Returns:
            tuple[list[dict], list[str]]: (todas las instancias encontradas en formato crudo de boto3,
            regiones en las que se encontró al menos una instancia).

        Raises:
            PermissionError: sin permisos para listar instancias EC2.
            Exception: cualquier otro fallo de la API. Los errores de una región concreta no detienen el
                escaneo de las demás (se loguean y se continúa).
        """

        try:
            if not self.session:
                raise Exception("No hay sesión activa. Ejecute connect() primero")

            all_instances = []
            regions_founded = []
            if regions == None or len(regions) == 0:
                ec2 = self.session.client('ec2')
                regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
            for r in regions:
                try:
                    logger.info(f"Scanning EC2 instances in region: {r}")
                    regional_ec2 = self.session.client('ec2', region_name=r)
                    instances = regional_ec2.describe_instances()
                    if instances['Reservations'] == []:
                        logger.info(f"No EC2 instances found in region: {r}")
                        continue
                    else:
                        regions_founded.append(r)
                        logger.info(f"Found {len(instances['Reservations'])} reservations in region: {r}")
                        for reservation in instances['Reservations']:
                            for instance in reservation['Instances']:
                                try:
                                    volumes = regional_ec2.describe_volumes(Filters=[{'Name': 'attachment.instance-id', 'Values': [instance['InstanceId']]}])
                                    list_volumes = []
                                    for v in volumes['Volumes']:
                                        list_volumes.append({
                                            "volume_id": v['VolumeId'],
                                            "encrypted": v['Encrypted']
                                        })
                                    instance['volumes'] = list_volumes
                                except ClientError:
                                    instance['volumes'] = None

                                try:
                                    sg_ids = [sg['GroupId'] for sg in instance.get('SecurityGroups', [])]
                                    if sg_ids:
                                        sg_details = regional_ec2.describe_security_groups(GroupIds=sg_ids)
                                        instance['SecurityGroupsDetails'] = sg_details['SecurityGroups']
                                    else:
                                        instance['SecurityGroupsDetails'] = []
                                except ClientError:
                                    instance['SecurityGroupsDetails'] = []

                                instance['public_ip'] = instance.get('PublicIpAddress', None)
                                all_instances.append(instance)

                except Exception as e:
                    logger.error(f"Error scanning EC2 instances in region {r}: {str(e)}")
                    continue
            logger.info(f"Total EC2 instances found across all regions: {len(all_instances)}")
            return all_instances, regions_founded

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError("Sin permisos para listar instancias EC2")
            raise Exception(f"Error al escanear EC2: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Error inesperado al escanear EC2: {str(e)}")



