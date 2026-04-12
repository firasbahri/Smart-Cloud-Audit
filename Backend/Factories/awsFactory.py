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
                userRoot = IAMUser(
                    id=u['UserId'],
                    name=u['UserName'],
                    service='IAM',
                    region='global',
                    access_keys=u.get('AccessKeyMetadata', []),
                    date=u.get('CreateDate', ''),
                    managed_policies=[],
                    inline_policies=[],
                    mfa_enabled=u.get('Mfa_enabled'),
                    password_last_used=u.get('PasswordLastUsed', None)
                )
                users.append(userRoot)

            else:
                inline_policies_normalized = []
                for p in u.get('InlinePolicies', []):
                    for s in p.get('PolicyDocument', {}).get('Statement', []):
                        logger.info(f"Normalizing inline policy {p['PolicyName']} for user {u['UserName']}")
                        inline_policies_normalized.append({
                            "policy_name": p["PolicyName"],
                            "actions": s.get("Action") if isinstance(s.get("Action"), list) else [s.get("Action")],
                            "resources": s.get("Resource") if isinstance(s.get("Resource"), list) else [s.get("Resource")],
                            "effect": s.get("Effect")
                        })

                user = IAMUser(
                    id=u['UserId'],
                    name=u['UserName'],
                    service='IAM',
                    region='global',
                    access_keys=u.get('AccessKeyMetadata', []),
                    date=u.get('CreateDate', ''),
                    managed_policies=[{"policy_name": p["PolicyName"]} for p in u.get('AttachedManagedPolicies', [])],
                    inline_policies=inline_policies_normalized,
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
            inline_policies_normalized = []
            for policy in g.get('InlinePolicies', []):
                for statement in policy.get('PolicyDocument', {}).get('Statement', []):
                    logger.info(f"Normalizing inline policy {policy['PolicyName']} for group {g['GroupName']}")
                    inline_policies_normalized.append({
                        "policy_name": policy["PolicyName"],
                        "actions": statement.get("Action") if isinstance(statement.get("Action"), list) else [statement.get("Action")],
                        "resources": statement.get("Resource") if isinstance(statement.get("Resource"), list) else [statement.get("Resource")],
                        "effect": statement.get("Effect")
                    })
            group = IAMGroup(
                id=g.get('GroupId', ''),
                name=g.get('GroupName', ''),
                service='IAM',
                region='global',
                Creation_date=g.get('CreateDate'),
                users=g.get('Users', []),
                managed_policies=[{"policy_name": p["PolicyName"]} for p in g.get('AttachedManagedPolicies', [])],
                inline_policies=inline_policies_normalized
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
                managed_policies=r.get('AttachedManagedPolicies', []),
                inline_policies=r.get('InlinePolicies', [])
            )
            roles.append(role)
        return roles
    
    @staticmethod
    def create_security_groups(securityGroupsRaw):
        security_groups = []
        for sg in securityGroupsRaw:
            logger.info(f"Creating security group ,{sg} ")
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
                public_ip=i.get('PublicIpAddress', None),
                state=i.get('State', {}).get('Name', ''),
                security_groups=AWSFactory.create_security_groups(i.get('SecurityGroupsDetails', [])),
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
              ip_ranges=[ip.get('CidrIp', '') for ip in r.get('IpRanges', [])]
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
                bucket_policy=b.get('Policies')
                
            )
            buckets.append(bucket)
        return buckets