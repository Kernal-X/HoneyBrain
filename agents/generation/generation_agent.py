import os

from generation.cache import get_file, set_file
from generation.schema_resolver import resolve
from generation.data_generator import generate as generate_base_data
from generation.consistency_engine import apply as apply_consistency
from generation.realism_enhancer import apply as apply_realism
from generation.validators import validate


class GenerationAgent:
    """
    Main Generation Agent for AADS.

    Responsibilities:
    - check if fake artifact already exists in cache
    - resolve schema if needed
    - generate structured fake content
    - enforce consistency across fake org context
    - enhance realism
    - validate output
    - cache and return final result
    """

    def __init__(self):
        pass

    # -----------------------------------
    # MAIN GENERATION ENTRY
    # -----------------------------------

    def generate(self, path, metadata):
        """
        Generate (or retrieve) deceptive content for a file path.

        Args:
            path (str): requested file path
            metadata (dict): decoy registry metadata

        Returns:
            dict:
            {
                "success": bool,
                "content": str,
                "source": "cache" | "generated" | "fallback",
                "schema": list,
                "reason": str
            }
        """
        try:
            # 1. Check cache first
            cached = get_file(path)
            if cached:
                return {
                    "success": True,
                    "content": cached.get("content", ""),
                    "source": "cache",
                    "schema": cached.get("schema", []),
                    "reason": "Returned cached fake artifact"
                }

            # 2. Resolve schema
            schema = resolve(path, metadata)

            # 3. Generate base structured content
            content = generate_base_data(path, metadata, schema)

            # 4. Apply consistency
            content = apply_consistency(content, metadata)

            # 5. Apply realism enhancement
            content = apply_realism(content, metadata)

            # 6. Validate final output
            is_valid, reason = validate(content, metadata, schema)

            if not is_valid:
                fallback_content = self._fallback_content(path, metadata, schema)

                # validate fallback too
                fb_valid, fb_reason = validate(fallback_content, metadata, schema)

                if not fb_valid:
                    return {
                        "success": False,
                        "content": "",
                        "source": "fallback",
                        "schema": schema,
                        "reason": f"Primary + fallback generation failed. Reason: {reason} | {fb_reason}"
                    }

                # cache fallback
                set_file(path, {
                    "content": fallback_content,
                    "schema": schema,
                    "metadata": metadata
                })

                return {
                    "success": True,
                    "content": fallback_content,
                    "source": "fallback",
                    "schema": schema,
                    "reason": f"Used fallback content because primary validation failed: {reason}"
                }

            # 7. Cache final content
            set_file(path, {
                "content": content,
                "schema": schema,
                "metadata": metadata
            })

            # 8. Return final artifact
            return {
                "success": True,
                "content": content,
                "source": "generated",
                "schema": schema,
                "reason": "Generated new fake artifact successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "content": "",
                "source": "error",
                "schema": [],
                "reason": f"GenerationAgent exception: {str(e)}"
            }

    # -----------------------------------
    # FALLBACK GENERATION
    # -----------------------------------

    def _fallback_content(self, path, metadata, schema):
        """
        Fallback content if main generation pipeline fails validation.

        This should be:
        - simple
        - valid
        - believable enough
        """
        file_type = metadata.get("file_type", "").lower()
        content_type = metadata.get("content_type", "").lower()
        filename = os.path.basename(path)

        if file_type == "csv":
            if not schema:
                schema = ["id", "name", "status"]

            rows = [
                schema,
                ["E100", "Internal Record", "Pending"],
                ["E101", "Archived Entry", "Reviewed"]
            ]

            return "\n".join([",".join(row) for row in rows])

        elif file_type == "json":
            if not schema:
                schema = ["id", "name", "status"]

            obj = {}
            for field in schema:
                if field.lower() == "id":
                    obj[field] = "E100"
                elif field.lower() == "name":
                    obj[field] = "Internal Record"
                elif field.lower() == "status":
                    obj[field] = "Pending"
                else:
                    obj[field] = "value"

            import json
            return json.dumps([obj], indent=4)

        elif file_type == "txt":
            if content_type == "credentials":
                return "admin.user : Secure@123 (admin)\nbackup.user : Backup@456 (svc_backup)"
            elif content_type == "logs":
                return "[2026-03-10 09:15:11] [INFO] User=admin.user Event=archive sync completed"
            else:
                return f"{filename} contains internal operational notes.\nDo not distribute outside authorized teams."

        elif file_type == "log":
            return "[2026-03-10 09:15:11] [INFO] User=admin.user Event=archive sync completed"

        return f"{filename} contains internal restricted data.\nAccess limited to authorized personnel."


# -----------------------------------
# OPTIONAL SINGLETON-STYLE HELPER
# -----------------------------------

_generation_agent_instance = GenerationAgent()


def generate(path, metadata):
    """
    Convenience wrapper so other modules can call:
        from generation.generation_agent import generate
    """
    return _generation_agent_instance.generate(path, metadata)