from Model.IAM_Model.IAMUser import IAMUser
from Model.IAM_Model.IAMGroup import IAMGroup
from Model.IAM_Model.IAMRole import IAMRole
from Model.EC2_Model.EC2 import EC2
from Model.s3Bucket import S3Bucket
from Model.EC2_Model.SecurityGroup import SecurityGroup
from Model.EC2_Model.Rule import Rule
import logging

logger = logging.getLogger(__name__)

class AWSFactory:
    @staticmethod
    def create_users(usersRaw):
        users = []
        for u in usersRaw:
           
            if u['UserName'] == 'root':
                logger.info("Creating root user")
                logger.info(f"mfa_enabled for root user: {u.get('MfaActive', False)}")
              
                userRoot = IAMUser(
                    id=u['UserId'],
                    name=u['UserName'],
                    service='IAM',
                    region='global',
                    groups=[],
                    access_keys=u.get('AccessKeyMetadata', []),
                    date=u.get('CreateDate', ''),
                    policies=u.get('AttachedManagedPolicies', []),
                    mfa_enabled=u.get('Mfa_enabled',),
                    password_last_used=u.get('PasswordLastUsed', None)
                )
             
                users.append(userRoot)
                
            else:   
                user = IAMUser(
                    id=u['UserId'],
                    name=u['UserName'],
                    service='IAM',
                    region='global',
                    groups=[],
                    access_keys=u.get('AccessKeyMetadata', []),
                    date=u.get('CreateDate', ''),
                    policies=u.get('AttachedManagedPolicies', []),
                    mfa_enabled=u.get('Mfa_enabled', False),
                    password_last_used=u.get('PasswordLastUsed', None)
                )
                logger.info(f"access_keys for user {user.name}: {user.access_keys}")
                users.append(user)
        return users
    
    @staticmethod
    def create_groups(groupsRaw):
        groups = []
        for g in groupsRaw:
            group = IAMGroup(
                id=g.get('GroupId', ''),
                name=g.get('GroupName', ''),
                service='IAM',
                region='global',
                Creation_date=g.get('CreateDate'),
                users=[],
                policies=g.get('AttachedManagedPolicies', [])
            )
            groups.append(group)
        return groups
    
    @staticmethod
    def create_roles(rolesRaw):
        roles = []
        for r in rolesRaw:
            role = IAMRole(
                id=r.get('RoleId', ''),
                name=r.get('RoleName', ''),
                service='IAM',
                region='global',
                Creation_date=r.get('CreateDate',''),
                assume_role_policy=r.get('AssumeRolePolicyDocument'),
                policies=r.get('AttachedManagedPolicies', [])
            )
            roles.append(role)
        return roles
    
    @staticmethod
    def create_security_groups(securityGroupsRaw):
        security_groups = []
        for sg in securityGroupsRaw:
            rules_created = AWSFactory.create_rules(sg.get('IpPermissions', []))
            security_group = SecurityGroup(
                id=sg['GroupId'],
                rules=rules_created
            )
            security_groups.append(security_group)
        return security_groups

    @staticmethod
    def create_ec2(ReservationRaw):
        instances = []
        for r in ReservationRaw:
            for i in r['Instances']:
                instance = EC2(
                    id=i.get('InstanceId', ''),
                    name=i.get('InstanceType', ''),
                    service='EC2',
                    region=i.get('Placement', {}).get('AvailabilityZone', ''),
                date=i.get('LaunchTime'),
                instance_type=i.get('InstanceType', ''),
                state=i.get('State', {}).get('Name', ''),
                security_groups=AWSFactory.create_security_groups(i.get('SecurityGroups', [])), 
                volumes=i.get('volumes')
            )
            instances.append(instance)
        return instances
    

    @staticmethod
    def create_rules(rulesRaw):
      rules = []
      for r in rulesRaw:
          rule = Rule(
              protocol=r.get('IpProtocol', ''),
              from_port=r.get('FromPort'),
              to_port=r.get('ToPort'),
              ip_ranges=r.get('IpRanges', [])
            )
          rules.append(rule)
      return rules
   
    @staticmethod
    def create_buckets(bucketsRaw):
        buckets = []
        for b in bucketsRaw:
            bucket = S3Bucket(
                id=b.get('Name', ''),
                name=b.get('Name', ''),
                service='S3',
                region=b.get('Region', ''),
                Creation_date=b.get('CreationDate', ''),
                public_access=b.get('PublicAccess'),
                versioning=b.get('Versioning'),
                encryption=b.get('Encryption'),
                policies=b.get('Policies')
                
            )
            buckets.append(bucket)
        return buckets