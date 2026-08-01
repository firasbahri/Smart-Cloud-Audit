import logging

logger = logging.getLogger(__name__)


def is_admin(policies: list) -> bool:
    """True if any managed policy in the list is exactly 'AdministratorAccess'."""
    for policy in policies:
        if policy.get("policy_name") == "AdministratorAccess":
            return True
    return False


def has_wildcard_permissions(inline_policies: list) -> list:
    """Returns the names of inline policies that Allow action '*' on resource '*'.

    Args:
        inline_policies (list): normalized inline policies (effect, actions, resources).

    Returns:
        list[str]: policy names that combine wildcard action and wildcard resource.
    """
    policies_with_wildcard = []
    for policy in inline_policies:
        if policy.get("effect") != "Allow":
            continue
        actions = policy.get("actions", [])
        resources = policy.get("resources", [])
        if "*" in actions and "*" in resources:
            policies_with_wildcard.append(policy.get("policy_name"))
    return policies_with_wildcard
