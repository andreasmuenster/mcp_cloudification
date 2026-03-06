# formatter.py
# TOON-Formatierung für SAP-Objekte

_FIELDS = [
    "tadirObject", "tadirObjName", "objectType", "objectKey",
    "softwareComponent", "applicationComponent", "state", "release", "fps",
]

def to_toon(obj):
    lines = [f"{field}: {obj.get(field, '')}" for field in _FIELDS]
    if obj.get("successors"):
        lines.append("successors:")
        lines.extend(
            f"  - {s.get('tadirObjName', '')} ({s.get('objectType', '')})"
            for s in obj["successors"]
        )
    return "\n".join(lines)
