from abc import ABC, abstractmethod

class IScanner(ABC):
    """Contrato que debe cumplir cualquier scanner de proveedor cloud (hoy solo AWS, pero pensado para Azure/GCP)."""

    def __init__(self, name):
        """Guarda el nombre del proveedor (ej. "AWS") que identifica a este scanner."""
        self.name = name

    def get_name(self):
        """Nombre del proveedor que escanea esta instancia."""
        return self.name


    @abstractmethod
    def get_resources(self) -> list:
        """Lista de tipos de recurso que este proveedor sabe escanear (ej. ["users", "groups", "ec2", "s3"])."""
        pass

    @abstractmethod
    def connect(self,identifier):
        """Abre sesión contra el proveedor a partir de un identificador (en AWS, el ARN del rol a asumir)."""
        pass
    @abstractmethod
    def scan_resource(self, resource):
        """Escanea un tipo de recurso concreto y devuelve sus datos crudos, tal como los entrega el proveedor."""
        pass

