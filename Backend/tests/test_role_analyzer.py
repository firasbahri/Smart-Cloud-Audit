from unittest.mock import MagicMock
from analyzer.IAM_Analyzer import IAMAnalyzer


def make_role(id, name, managed_policies, inline_policies, trusted_entities):
    role = MagicMock()
    role.id = id
    role.name = name
    role.managed_policies = managed_policies
    role.inline_policies = inline_policies
    role.trusted_entities = trusted_entities
    return role


def test_role_no_vulnerabilities():
    analyzer = IAMAnalyzer()
    role = make_role("role-1", "TestRole", [], [], [])
    result = analyzer.check_role_permissions([role])
    assert len(result) == 0


def test_role_admin_managed_policy():
    analyzer = IAMAnalyzer()
    role = make_role("role-2", "AdminRole",
        managed_policies=[{"policy_name": "AdministratorAccess"}],
        inline_policies=[],
        trusted_entities=[]
    )
    result = analyzer.check_role_permissions([role])
    assert len(result) == 1
    assert result[0].id == f"iam_role_{role.id}_managed_admin"
    assert result[0].severity == "Medium"


def test_role_wildcard_inline_policy():
    analyzer = IAMAnalyzer()
    role = make_role("role-3", "WildcardRole",
        managed_policies=[],
        inline_policies=[{"policy_name": "WildcardPolicy", "actions": ["*"], "resources": ["*"], "effect": "Allow"}],
        trusted_entities=[]
    )
    result = analyzer.check_role_permissions([role])
    assert len(result) == 1
    assert result[0].id == f"iam_role_{role.id}_inline_WildcardPolicy_wildcard"
    assert result[0].severity == "High"


def test_role_admin_with_trusted_entities():
    analyzer = IAMAnalyzer()
    role = make_role("role-4", "AdminTrustedRole",
        managed_policies=[{"policy_name": "AdministratorAccess"}],
        inline_policies=[],
        trusted_entities=[{"entity": ("AWS", "arn:aws:iam::123456789012:root")}]
    )
    result = analyzer.check_role_permissions([role])
    assert len(result) == 1
    assert result[0].id == f"iam_role_{role.id}_managed_admin_trusted"
    assert result[0].severity == "Critical"


def test_role_wildcard_with_trusted_entities():
    analyzer = IAMAnalyzer()
    role = make_role("role-5", "WildcardTrustedRole",
        managed_policies=[],
        inline_policies=[{"policy_name": "WildcardPolicy", "actions": ["*"], "resources": ["*"], "effect": "Allow"}],
        trusted_entities=[{"entity": ("AWS", "arn:aws:iam::123456789012:root")}]
    )
    result = analyzer.check_role_permissions([role])
    assert len(result) == 1
    assert result[0].id == f"iam_role_{role.id}_inline_WildcardPolicy_wildcard_trusted"
    assert result[0].severity == "Critical"
