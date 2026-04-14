from analyzer.ec2_analyzer import EC2Analyzer
from unittest.mock import MagicMock


def make_instance(id,volumes,tags):
  instance = MagicMock()
  instance.id = id
  instance.volumes = volumes
  instance.tags = tags
  return instance

def test_check_ebs_encryption():
    analyzer = EC2Analyzer()
    instance1 = make_instance("i-1234567890abcdef0", [{"VolumeId": "vol-1234567890abcdef0", "Encrypted": False}])
    instance2 = make_instance("i-0987654321abcdef0", [{"VolumeId": "vol-0987654321abcdef0", "Encrypted": True}])
    instance3 = make_instance("i-1122334455667788", [{"VolumeId": "vol-1122334455667788", "Encrypted": False}, {"VolumeId": "vol-1122334455667789", "Encrypted": True}])

    instances = [instance1, instance2, instance3]
    vulnerabilities = analyzer.check_ebs_encryption(instances)
    assert len(vulnerabilities) == 2
    assert vulnerabilities[0].id == f"ec2_{instance1.id}_ebs_{instance1.volumes[0]['VolumeId']}_unencrypted"
    assert vulnerabilities[0].name == "EC2 Instance with Unencrypted EBS Volume"


def test_check_tags():
    analyzer = EC2Analyzer()
    instance1 = make_instance("i-1234567890abcdef0", [], [])
    result= analyzer.check_tags([instance1])
    assert len(result) == 1
    assert result[0].id == f"ec2_{instance1.id}_missing_tags"