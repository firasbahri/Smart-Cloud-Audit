from analyzer.IAnalyzer import IAnalyzer
from analyzer.IAM_Analyzer import IAMAnalyzer
from analyzer.ec2_analyzer import EC2Analyzer
from analyzer.s3_analyzer import S3Analyzer
import logging

logger = logging.getLogger(__name__)


class AWSAnalyzer(IAnalyzer):
    """Orquesta los analizadores estáticos de AWS (IAM, EC2, S3) y junta sus resultados en una sola auditoría."""

    def __init__(self):
        """Crea una instancia de cada analizador concreto que se va a usar en analyze()."""
        self.iamAnalyzer = IAMAnalyzer()
        self.ec2Analyzer = EC2Analyzer()
        self.s3Analyzer = S3Analyzer()

    def analyze(self, resources: dict):
        """Pasa cada tipo de recurso por su analizador correspondiente y devuelve todas las vulnerabilidades juntas.

        Args:
            resources (dict): diccionario con las claves "users", "groups", "roles", "ec2" y "buckets",
                cada una con la lista de recursos de ese tipo (puede venir vacía si el scan no encontró nada).

        Returns:
            list[Vulnerability]: la unión de lo que detectan IAMAnalyzer, EC2Analyzer y S3Analyzer.

        Example:
            >>> AWSAnalyzer().analyze({"users": [...], "groups": [], "roles": [], "ec2": [...], "buckets": []})
            [Vulnerability(...), Vulnerability(...)]
        """
        vulnerabilities = []
        users = resources.get("users", [])
        groups = resources.get("groups", [])
        instances = resources.get("ec2", [])
        buckets = resources.get("buckets", [])
        roles = resources.get("roles", [])

        try:
            vulnerabilities.extend(self.iamAnalyzer.analyze(users, groups, roles))
            vulnerabilities.extend(self.ec2Analyzer.analyze(instances))
            vulnerabilities.extend(self.s3Analyzer.analyze(buckets))

            logger.info(f"Completed analysis. Found {len(vulnerabilities)} vulnerabilities.")
        except Exception as e:
            logger.error(f"Error analyzing AWS resources: {e}")
            raise

        return vulnerabilities
