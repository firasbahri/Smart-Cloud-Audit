from analyzer.ec2_analyzer import EC2Analyzer
from unittest.mock import MagicMock


def make_instance(id,volumes):
  instance = MagicMock()
  instance.id = id
  instance.volumes = volumes
  return instance

def test_check_ebs_encryption():
    analyzer = EC2Analyzer()
    instance1 = make_instance("i-1234567890abcdef0", [{"Encrypted": False}])
    instance2= make_instance("i-0987654321abcdef0", [{"Encrypted": True}])
    instance3= make_instance("i-1122334455667788", [{"Encrypted": False}, {"Encrypted": True}])

    instances = [instance1, instance2, instance3]
    vulnerabilities = analyzer.check_ebs_encryption(instances)
    assert len(vulnerabilities) == 2
    assert vulnerabilities[0].id == "ec2_i-1234567890abcdef0"
    assert vulnerabilities[0].name == "EC2 Instance with Unencrypted EBS Volume"
