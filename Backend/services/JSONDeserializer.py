from datetime import datetime

from Model.EC2_Model.EC2 import EC2
from Model.EC2_Model.Rule import Rule
from Model.EC2_Model.SecurityGroup import SecurityGroup
from Model.IAM_Model.IAMGroup import IAMGroup
from Model.IAM_Model.IAMRole import IAMRole
from Model.IAM_Model.IAMUser import IAMUser
from Model.s3Bucket import S3Bucket


class JSONDeserializer:
    @staticmethod
    def parse_datetime(value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def deserialize_iam_user(raw):
        if isinstance(raw, IAMUser):
            return raw
        if not isinstance(raw, dict):
            return None

        parsed_access_keys = []
        for access_key in raw.get("access_keys", []):
            if not isinstance(access_key, dict):
                continue
            access_key_dict = dict(access_key)
            access_key_dict["CreateDate"] = JSONDeserializer.parse_datetime(access_key_dict.get("CreateDate"))
            parsed_access_keys.append(access_key_dict)

        return IAMUser(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            service=raw.get("service", "IAM"),
            region=raw.get("region", "global"),
            access_keys=parsed_access_keys,
            date=JSONDeserializer.parse_datetime(raw.get("date")),
            managed_policies=raw.get("managed_policies", []),
            inline_policies=raw.get("inline_policies", []),
            mfa_enabled=raw.get("mfa_enabled", False),
            password_last_used=JSONDeserializer.parse_datetime(raw.get("password_last_used")),
        )

    @staticmethod
    def deserialize_iam_group(raw):
        if isinstance(raw, IAMGroup):
            return raw
        if not isinstance(raw, dict):
            return None

        return IAMGroup(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            service=raw.get("service", "IAM"),
            region=raw.get("region", "global"),
            Creation_date=JSONDeserializer.parse_datetime(raw.get("date")),
            users=raw.get("users", []),
            managed_policies=raw.get("managed_policies", []),
            inline_policies=raw.get("inline_policies", []),

        )

    @staticmethod
    def deserialize_iam_role(raw):
        if isinstance(raw, IAMRole):
            return raw
        if not isinstance(raw, dict):
            return None

        return IAMRole(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            service=raw.get("service", "IAM"),
            region=raw.get("region", "global"),
            Creation_date=JSONDeserializer.parse_datetime(raw.get("date")),
            assume_role_policy=raw.get("assume_role_policy"),
            managed_policies=raw.get("managed_policies", []),
            inline_policies=raw.get("inline_policies", []),
        )

    @staticmethod
    def deserialize_rule(raw):
        if isinstance(raw, Rule):
            return raw
        if not isinstance(raw, dict):
            return None

        return Rule(
            protocol=raw.get("protocol", ""),
            from_port=raw.get("from_port"),
            to_port=raw.get("to_port"),
            ip_ranges=raw.get("ip_ranges", []),
        )

    @staticmethod
    def deserialize_security_group(raw):
        if isinstance(raw, SecurityGroup):
            return raw
        if not isinstance(raw, dict):
            return None

        rules = [
            rule
            for rule in (
                JSONDeserializer.deserialize_rule(item)
                for item in raw.get("rules", [])
            )
            if rule is not None
        ]

        return SecurityGroup(
            id=raw.get("id", ""),
            rules=rules,
        )

    @staticmethod
    def deserialize_ec2(raw):
        if isinstance(raw, EC2):
            return raw
        if not isinstance(raw, dict):
            return None

        security_groups = [
            security_group
            for security_group in (
                JSONDeserializer.deserialize_security_group(item)
                for item in raw.get("security_groups", [])
            )
            if security_group is not None
        ]

        return EC2(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            service=raw.get("service", "EC2"),
            region=raw.get("region", ""),
            date=JSONDeserializer.parse_datetime(raw.get("date")),
            instance_type=raw.get("instance_type", ""),
            state=raw.get("state", ""),
            security_groups=security_groups,
            volumes=raw.get("volumes"),
        )

    @staticmethod
    def deserialize_s3_bucket(raw):
        if isinstance(raw, S3Bucket):
            return raw
        if not isinstance(raw, dict):
            return None

        return S3Bucket(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            service=raw.get("service", "S3"),
            region=raw.get("region", ""),
            Creation_date=JSONDeserializer.parse_datetime(raw.get("date")),
            bucket_policy=raw.get("bucket_policy"),
            versioning=raw.get("versioning"),
            encryption=raw.get("encryption"),
            public_access=raw.get("public_access"),
        )

    @staticmethod
    def deserialize_resources(resources):
        if not isinstance(resources, dict):
            return {}

        deserialized = dict(resources)

        deserialized["users"] = [
            user
            for user in (
                JSONDeserializer.deserialize_iam_user(item)
                for item in resources.get("users", [])
            )
            if user is not None
        ]
        deserialized["groups"] = [
            group
            for group in (
                JSONDeserializer.deserialize_iam_group(item)
                for item in resources.get("groups", [])
            )
            if group is not None
        ]
        deserialized["roles"] = [
            role
            for role in (
                JSONDeserializer.deserialize_iam_role(item)
                for item in resources.get("roles", [])
            )
            if role is not None
        ]
        deserialized["buckets"] = [
            bucket
            for bucket in (
                JSONDeserializer.deserialize_s3_bucket(item)
                for item in resources.get("buckets", [])
            )
            if bucket is not None
        ]
        deserialized["ec2"] = [
            instance
            for instance in (
                JSONDeserializer.deserialize_ec2(item)
                for item in resources.get("ec2", [])
            )
            if instance is not None
        ]

        return deserialized
