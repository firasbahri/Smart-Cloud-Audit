from Model.resource import Resource


class S3Bucket(Resource):
    """
    Representa un bucket S3.

    Campos de seguridad añadidos:
    - block_public_acls / ignore_public_acls / block_public_policy / restrict_public_buckets:
      reemplazan el campo único public_access con los 4 controles granulares de Block Public Access.
      Tener cualquiera en False puede exponer objetos públicamente aunque haya bucket policy restrictiva.
    - acl_grantees: concesiones ACL del bucket. Si incluye 'AllUsers' o 'AuthenticatedUsers'
      el bucket puede ser listado o escrito públicamente sin pasar por la bucket policy.
    - logging / logging_target_bucket: sin logging de acceso no hay trazabilidad de quién leyó
      o modificó objetos (requerido por CIS AWS Benchmark 2.6).
    - object_lock: sin object lock los objetos pueden ser borrados permanentemente,
      incluyendo por ransomware o credenciales comprometidas.
    - mfa_delete: sin MFA para eliminar versiones, cualquier credencial comprometida
      puede purgar el historial completo de versiones.
    - lifecycle: ausencia de reglas de ciclo de vida supone retención indefinida de datos,
      con el riesgo de exposición prolongada de información sensible y costes no controlados.
    - replication_rules: sin replicación cross-region no hay recuperación ante fallo de región.
    - notification_config: sin notificaciones no hay alertas automáticas ante eventos críticos
      (subida de objetos, eliminaciones, cambios de ACL).
    """

    def __init__(self, id, name, service, region, Creation_date, bucket_policy, versioning,
                 encryption, public_access=None,
                 block_public_acls=None, ignore_public_acls=None,
                 block_public_policy=None, restrict_public_buckets=None,
                 acl_grantees=None, logging=False, logging_target_bucket=None,
                 object_lock=False, mfa_delete=False,
                 lifecycle=None, replication_rules=None, notification_config=None):
        super().__init__(id, name, service, region, Creation_date)
        self.bucket_policy = bucket_policy
        self.versioning = versioning
        self.encryption = encryption
        # public_access mantenido por compatibilidad con scans anteriores en MongoDB
        self.public_access = public_access
        # Block Public Access granular — 🟠 alto
        self.block_public_acls = block_public_acls
        self.ignore_public_acls = ignore_public_acls
        self.block_public_policy = block_public_policy
        self.restrict_public_buckets = restrict_public_buckets
        # ACL grantees — 🔴 crítico
        self.acl_grantees = acl_grantees if acl_grantees is not None else []
        # Logging — 🔴 crítico
        self.logging = logging
        self.logging_target_bucket = logging_target_bucket
        # Protección de datos — 🟠 alto
        self.object_lock = object_lock
        self.mfa_delete = mfa_delete
        # Gestión del ciclo de vida — 🟡 medio
        self.lifecycle = lifecycle if lifecycle is not None else []
        self.replication_rules = replication_rules if replication_rules is not None else []
        self.notification_config = notification_config if notification_config is not None else {}
