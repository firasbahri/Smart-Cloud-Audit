import logging
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class EC2Analyzer:
    """Reglas de seguridad estáticas para instancias EC2: IP pública, puertos abiertos, EBS sin cifrar y etiquetado."""

    def analyze(self, instances: list) -> list:
        """Pasa las instancias por las cuatro comprobaciones y devuelve todos los hallazgos juntos.

        Args:
            instances (list): instancias EC2 del modelo de dominio, con security_groups y volumes ya resueltos.

        Returns:
            list[Vulnerability]: unión de check_public_ip, check_security_groups, check_ebs_encryption y check_tags.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_public_ip(instances))
        vulnerabilities.extend(self.check_security_groups(instances))
        vulnerabilities.extend(self.check_ebs_encryption(instances))
        vulnerabilities.extend(self.check_tags(instances))
        return vulnerabilities

    def check_public_ip(self, instances: list) -> list:
        """Marca las instancias que tienen una IP pública asignada (severidad Medium: amplía la superficie de ataque,
        aunque no implica por sí sola que haya un puerto abierto)."""
        vulnerabilities = []
        for instance in instances:
            if instance.public_ip is not None:
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_public_ip",
                    name="Instancia EC2 con IP Pública",
                    description=(
                        f"La instancia EC2 '{instance.id}' tiene una dirección IP pública ({instance.public_ip}), "
                        "lo que la expone directamente a internet y amplía la superficie de ataque."
                    ),
                    severity="Medium",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities


    def check_security_groups(self, instances: list) -> list:
        """Recorre los grupos de seguridad de cada instancia buscando reglas de entrada TCP que dejen SSH (22) o
        RDP (3389) abiertos a 0.0.0.0/0 — es decir, accesibles desde cualquier IP de internet.

        Args:
            instances (list): instancias EC2 con security_groups -> rules ya resueltos.

        Returns:
            list[Vulnerability]: severidad High por cada puerto SSH/RDP abierto al mundo que se encuentre.
        """
        Vulnerabilities = []
        for instance in instances:
            for sg in instance.security_groups:
                for rule in sg.rules:
                    if rule.protocol == "tcp" and rule.from_port == 22 and rule.to_port == 22:
                        for ip_range in rule.ip_ranges:
                            if ip_range == "0.0.0.0/0":
                                Vulnerabilities.append(Vulnerability(
                                    id=f"ec2_{instance.id}_sg_{sg.id}_open_ssh",
                                    name="Instancia EC2 con Puerto SSH Abierto",
                                    description=(
                                        f"La instancia EC2 '{instance.id}' tiene un grupo de seguridad '{sg.id}' "
                                        "que permite el acceso SSH desde cualquier dirección IP."
                                    ),
                                    severity="High",
                                    resource_id=instance.id,
                                    resource_type="EC2 Instance",
                                ))
                    if rule.protocol == "tcp" and rule.from_port == 3389 and rule.to_port == 3389:
                        for ip_range in rule.ip_ranges:
                            if ip_range == "0.0.0.0/0":
                                Vulnerabilities.append(Vulnerability(
                                    id=f"ec2_{instance.id}_sg_{sg.id}_open_rdp",
                                    name="Instancia EC2 con Puerto RDP Abierto",
                                    description=(
                                        f"La instancia EC2 '{instance.id}' tiene un grupo de seguridad '{sg.id}' "
                                        "que permite el acceso RDP desde cualquier dirección IP."
                                    ),
                                    severity="High",
                                    resource_id=instance.id,
                                    resource_type="EC2 Instance",
                                ))
        return Vulnerabilities



    def check_ebs_encryption(self, instances: list) -> list:
        """Detecta volúmenes EBS adjuntos sin cifrar (Encrypted=False). Si el volumen físico se compromete o se
        clona, los datos quedan legibles sin necesidad de ninguna credencial.

        Args:
            instances (list): instancias EC2 con la lista volumes ya resuelta (volume_id + encrypted).

        Returns:
            list[Vulnerability]: una entrada por cada volumen sin cifrar encontrado, severidad Medium.
        """
        vulnerabilities = []
        for instance in instances:
            for volume in instance.volumes:
                logger.info(f"volumes of instance {instance.id}: {volume}")
                if volume["encrypted"] == False:
                    vulnerabilities.append(Vulnerability(
                        id=f"ec2_{instance.id}_ebs_{volume['volume_id']}_unencrypted",
                        name="Instancia EC2 con Volumen EBS sin Cifrar",
                        description=(
                            f"La instancia EC2 '{instance.id}' tiene un volumen EBS '{volume['volume_id']}' adjunto "
                            "que no está cifrado, lo que puede provocar exposición de datos si el volumen se ve comprometido."
                        ),
                        severity="Medium",
                        resource_id=instance.id,
                        resource_type="EC2 Instance",
                    ))
        return vulnerabilities


    def check_tags(self, instances: list) -> list:
        """Comprueba que cada instancia tenga las etiquetas Name, Environment y Owner. No es un riesgo de seguridad
        directo, pero sin esas etiquetas es fácil perder de vista qué recurso pertenece a quién (severidad Low).
        """
        vulnerabilities = []
        REQUIRED_TAGS = ["Name", "Environment", "Owner"]
        for instance in instances:
            tags_keys = [tag['Key'] for tag in instance.tags]
            missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags_keys]
            if missing_tags:
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_missing_tags",
                    name="Instancia EC2 con Etiquetas Faltantes",
                    description=(
                        f"La instancia EC2 '{instance.id}' no tiene todas las etiquetas requeridas, "
                        "lo que puede dificultar la gestión e identificación eficaz de los recursos."
                    ),
                    severity="Low",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities
