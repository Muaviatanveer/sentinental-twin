import hashlib
import yaml
from typing import Any

class ComposeParser:
    @staticmethod
    def parse(yaml_content: str) -> dict[str, Any]:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {str(e)}")
        
        if not isinstance(data, dict) or "services" not in data:
            raise ValueError("Invalid Compose file: missing 'services' block.")

        services = data.get("services", {})
        networks = data.get("networks", {})
        warnings = []

        # Validate and flag unsupported features for the twin runner
        for svc_name, svc_def in services.items():
            if "build" in svc_def:
                warnings.append(f"Service '{svc_name}' uses 'build'. Twin engine relies on pre-built images.")
            if "volumes" in svc_def:
                warnings.append(f"Service '{svc_name}' mounts volumes. Host mounts are stripped in sandbox.")
            if "privileged" in svc_def and svc_def["privileged"]:
                warnings.append(f"Service '{svc_name}' requests privileged mode. Denied in sandbox.")

        # Ensure 'default' network exists implicitly if not defined
        if not networks:
            networks = {"default": {"driver": "bridge"}}

        return {
            "services": services,
            "networks": networks,
            "warnings": warnings,
            "hash": hashlib.sha256(yaml_content.encode("utf-8")).hexdigest()
        }