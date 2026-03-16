from Model.IAM_Model.IAMUser import IAMUser
from Model.IAM_Model.IAMGroup import IAMGroup
from Model.IAM_Model.IAMRole import IAMRole
from Model.EC2_Model.EC2 import EC2
from Model.EC2_Model.SecurityGroup import SecurityGroup
from Model.EC2_Model.Rule import Rule


class ResourceFactory:
    @staticmethod
    def create_users(usersRaw):
        users = []
        for u in usersRaw:
           
            if u['UserName'] == 'root':
                print("hola")
                userRoot = IAMUser(
                    id=u['UserId'],
                    description=u['UserName'],
                    service='IAM',
                    region='global',
                    groups=[],
                    access_keys=u.get('AccessKeysPresent', 0),
                    date=u.get('CreateDate', ''),
                    policies=[],
                    mfa_enabled=u.get('MfaActive', False)
                )
                users.append(userRoot)
                
            else:
                print("hola2")
               
                user = IAMUser(
                    id=u['UserId'],
                    description=u['UserName'],
                    service='IAM',
                    region='global',
                    groups=[],
                    access_keys=u.get('AccessKeyMetadata', []),
                    date=u.get('CreateDate', ''),
                    policies=u.get('AttachedManagedPolicies', []),
                    mfa_enabled=u.get('MFADevices', [])
                )
                users.append(user)
        return users
    
    @staticmethod
    def create_groups(groupsRaw):
        groups = []
        for g in groupsRaw:
            group = IAMGroup(
                id=g.get('GroupId', ''),
                description=g.get('GroupName', ''),
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
                description=r.get('RoleName', ''),
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
            rules_created = ResourceFactory.create_rules(sg.get('IpPermissions', []))
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
                    description=i.get('InstanceType', ''),
                    service='EC2',
                    region=i.get('Placement', {}).get('AvailabilityZone', ''),
                date=i.get('LaunchTime'),
                instance_type=i.get('InstanceType', ''),
                state=i.get('State', {}).get('Name', ''),
                security_groups=ResourceFactory.create_security_groups(i.get('SecurityGroups', [])), 
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
   