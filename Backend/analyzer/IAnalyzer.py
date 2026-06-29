from abc import ABC, abstractmethod

class IAnalyzer(ABC):
    """Contrato que debe cumplir cualquier analizador de seguridad, sea para AWS, Azure o el proveedor que se añada más adelante."""

    @abstractmethod
    async def analyze(self, resources:list):
        """Analiza los recursos de un proveedor cloud y devuelve las vulnerabilidades encontradas.

        Args:
            resources (list): recursos ya convertidos a los modelos de dominio (no el JSON crudo del proveedor).

        Returns:
            list[Vulnerability]: una entrada por cada hallazgo de seguridad detectado.
        """
        pass
