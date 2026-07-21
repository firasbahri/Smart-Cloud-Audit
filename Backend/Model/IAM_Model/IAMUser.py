from Model.resource import Resource


class IAMUser(Resource):
    """
    Representa un usuario IAM.

    Campos de seguridad añadidos:
    - console_access: True si el usuario tiene login profile y puede autenticarse en la consola AWS.
      Un usuario con console_access=True y sin MFA es una cuenta comprometible por fuerza bruta
      o phishing de credenciales.
    - mfa_devices: lista de dispositivos MFA con su tipo ('virtual' o 'hardware'). Más detallado
      que el bool mfa_enabled; permite detectar ausencia total de MFA, uso de MFA de menor
      seguridad (virtual vs hardware), o usuarios con múltiples dispositivos activos.
    - mfa_enabled: mantenido por compatibilidad con scans anteriores almacenados en MongoDB.
    - tags: etiquetas del usuario. Permiten checks de gobernanza (p.ej. todos los usuarios deben
      tener tag 'owner') y auditorías de cobertura de etiquetado.
    """

    def __init__(self, id, name, service, region, access_keys, date, managed_policies,
                 inline_policies, mfa_enabled, password_last_used,
                 console_access=None, mfa_devices=None, tags=None):
        super().__init__(id, name, service, region, date)
        self.access_keys = access_keys
        self.managed_policies = managed_policies
        self.inline_policies = inline_policies
        self.mfa_enabled = mfa_enabled
        self.password_last_used = password_last_used
        # Acceso a consola — 🔴 crítico
        self.console_access = console_access
        # Dispositivos MFA con tipo — 🟠 alto
        self.mfa_devices = mfa_devices if mfa_devices is not None else []
        # Etiquetas — 🟡 medio
        self.tags = tags if tags is not None else []

    def get_access_keys(self):
        return self.access_keys
