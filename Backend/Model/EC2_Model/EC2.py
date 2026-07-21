from ..resource import Resource


class EC2(Resource):
    """
    Representa una instancia EC2.

    Campos de seguridad añadidos:
    - http_tokens / http_endpoint: configuración IMDSv2. Si http_tokens='optional', la instancia
      es vulnerable a SSRF que roba credenciales vía el endpoint de metadatos (169.254.169.254).
    - instance_profile: rol IAM adjunto (dict con Arn e Id). Una instancia expuesta a internet con
      perfil IAM permite escalar privilegios dentro de la cuenta si es comprometida.
    - user_data: script de arranque (texto plano). Suele contener secretos hardcodeados
      (contraseñas, tokens de API, claves privadas).
    - monitoring_state: monitoreo detallado de CloudWatch. Sin él, los incidentes de seguridad
      son más difíciles de detectar y correlacionar.
    - virtualization_type: 'paravirtual' indica virtualización obsoleta con menor aislamiento
      de hardware; 'hvm' es el estándar seguro actual.
    - private_ip / subnet_id: permiten determinar la topología de red y la exposición real
      de la instancia (p.ej. instancia en subred pública con perfil IAM adjunto).
    """

    def __init__(self, id, name, service, region, date, instance_type, public_ip, state,
                 security_groups, volumes, tags,
                 http_tokens=None, http_endpoint=None, instance_profile=None,
                 user_data=None, monitoring_state=None, virtualization_type=None,
                 private_ip=None, subnet_id=None):
        super().__init__(id, name, service, region, date)
        self.instance_type = instance_type
        self.public_ip = public_ip
        self.state = state
        self.security_groups = security_groups
        self.volumes = volumes
        self.tags = tags
        # IMDSv2 — 🔴 crítico
        self.http_tokens = http_tokens
        self.http_endpoint = http_endpoint
        # Perfil IAM adjunto — 🔴 crítico
        self.instance_profile = instance_profile
        # Script de arranque — 🟠 alto
        self.user_data = user_data
        # Monitoreo detallado — 🟡 medio
        self.monitoring_state = monitoring_state
        # Tipo de virtualización — 🟡 medio
        self.virtualization_type = virtualization_type
        # Red — 🟡 medio
        self.private_ip = private_ip
        self.subnet_id = subnet_id
