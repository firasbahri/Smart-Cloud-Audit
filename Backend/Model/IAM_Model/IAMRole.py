from Model.resource import Resource


class IAMRole(Resource):
    """
    Representa un rol IAM.

    Campos de seguridad añadidos:
    - permissions_boundary: política que limita el máximo de permisos efectivos del rol,
      independientemente de las políticas adjuntas. Sin permissions boundary, un rol con
      permisos amplios puede ser explotado para escalar privilegios dentro de la cuenta
      (p.ej. crear un nuevo usuario admin o adjuntarse AdministratorAccess).
    - is_service_role: True si el rol es asumible exclusivamente por un servicio AWS
      (ec2.amazonaws.com, lambda.amazonaws.com, etc.). Distingue roles de servicio de roles
      cross-account; estos últimos tienen un perfil de riesgo mayor al ser asumibles
      desde fuera de la cuenta.
    - tags: etiquetas del rol. Útiles para checks de gobernanza y cobertura de etiquetado.
    """

    def __init__(self, id, name, service, region, Creation_date, assume_role_policy,
                 managed_policies, inline_policies, trusted_entities,
                 permissions_boundary=None, is_service_role=False, tags=None):
        super().__init__(id, name, service, region, Creation_date)
        self.assume_role_policy = assume_role_policy
        self.managed_policies = managed_policies
        self.inline_policies = inline_policies
        self.trusted_entities = trusted_entities
        # Límite de permisos — 🔴 crítico
        self.permissions_boundary = permissions_boundary
        # Tipo de rol — 🟠 alto
        self.is_service_role = is_service_role
        # Etiquetas — 🟡 medio
        self.tags = tags if tags is not None else []

    def get_assume_role_policy(self):
        return self.assume_role_policy
