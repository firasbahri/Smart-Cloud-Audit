from analyzer.iam_user_analyzer import IAMUserAnalyzer
from analyzer.iam_group_analyzer import IAMGroupAnalyzer
from analyzer.iam_role_analyzer import IAMRoleAnalyzer


class IAMAnalyzer:
    """Orchestrates the three IAM sub-analyzers (users, groups, roles) and merges their findings.

    aws_analyzer.py calls this class directly; the three sub-analyzers are the ones that
    contain the actual check logic. Keeping this facade means no change is needed in
    aws_analyzer.py or the controller when individual sub-analyzers are extended.
    """

    def __init__(self):
        self.user_analyzer = IAMUserAnalyzer()
        self.group_analyzer = IAMGroupAnalyzer()
        self.role_analyzer = IAMRoleAnalyzer()

    def analyze(self, users: list, groups: list, roles: list) -> list:
        """Run all IAM checks and return the combined findings.

        Args:
            users (list): IAM users from the domain model (root user expected at index 0).
            groups (list): IAM groups from the domain model.
            roles (list): IAM roles from the domain model.

        Returns:
            list[Vulnerability]: union of findings from all three sub-analyzers.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.user_analyzer.analyze(users))
        vulnerabilities.extend(self.group_analyzer.analyze(groups))
        vulnerabilities.extend(self.role_analyzer.analyze(roles))
        return vulnerabilities
