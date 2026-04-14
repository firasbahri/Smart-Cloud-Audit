from unittest.mock import MagicMock
from analyzer.s3_analyzer import S3Analyzer




def make_bucket(id, name, bucket_policy, public_access):
    bucket = MagicMock()
    bucket.id = id
    bucket.name = name
    bucket.bucket_policy = bucket_policy
    bucket.public_access = public_access
    return bucket

def test_bucket_public_access_only():
    analyzer = S3Analyzer()
    bucket = make_bucket("bucket-1", "TestBucket", {"Statement": []}, [])
    result = analyzer.check_public_access([bucket])
    assert len(result) == 1
    assert result[0].id == f"s3_{bucket.id}_public_access_only"
    assert result[0].severity == "Medium"


def test_bucket_public_policy_only():
    analyzer = S3Analyzer()
    bucket = make_bucket("bucket-2", "TestBucket2", {"Statement": [{"Effect": "Allow", "Principal": "*", "Action": "*", "Resource": "*"}]}, [])
    result = analyzer.check_public_access([bucket])
    assert len(result) == 1
    assert result[0].id == f"s3_{bucket.id}_public_policy_only"

    bucket_no_public_access = make_bucket("bucket-3", "TestBucket3", {"Statement": [{"Effect": "Allow", "Principal": {"AWS": "*"}, "Action": "*", "Resource": "*"}]}, [])
    result_no_public_access = analyzer.check_public_access([bucket_no_public_access])
    assert len(result_no_public_access) == 1
    assert result_no_public_access[0].id == f"s3_{bucket_no_public_access.id}_public_policy_only"
    assert result_no_public_access[0].severity == "Medium"

def test_bucket_public_access_and_policy():
    analyzer= S3Analyzer()
    bucket = make_bucket("bucket-4", "TestBucket4", {"Statement": [{"Effect": "Allow", "Principal": "*", "Action": "*", "Resource": "*"}]}, [{ "BlockPublicAcls": False,
    "IgnorePublicAcls": False,
    "BlockPublicPolicy": False,
    "RestrictPublicBuckets": False}])
    result = analyzer.check_public_access([bucket])
    assert len(result) == 1
    assert result[0].id == f"s3_{bucket.id}_public_access_policy_and_public_access"
    assert result[0].severity == "Critical"

    bucket2= make_bucket("bucket-5", "TestBucket5", {"Statement": [{"Effect": "Allow", "Principal": {"AWS": "*"}, "Action": "*", "Resource": "*"}]}, [{ "BlockPublicAcls": False,
    "IgnorePublicAcls": False,
    "BlockPublicPolicy": True,
    "RestrictPublicBuckets": False}])
    result2 = analyzer.check_public_access([bucket2])
    assert len(result2) == 1
    assert result2[0].id == f"s3_{bucket2.id}_public_access_policy_and_public_access"
    assert result2[0].severity == "Critical"

def test_bucket_no_vulnerabilities():
    analyzer = S3Analyzer()
    bucket = make_bucket("bucket-6", "TestBucket6", {"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "*", "Resource": "*"}]}, [{ "BlockPublicAcls": True,
    "IgnorePublicAcls": True,
    "BlockPublicPolicy": True,
    "RestrictPublicBuckets": True}])
    result = analyzer.check_public_access([bucket])
    assert len(result) == 0

