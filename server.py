# server.py
#---------------------------------------------------------------------------------------------------------------------------
# Stellt die Cloudification-Repository-Suche, implementiert mit FastMCP, zur Verfügung.
# Dieses Tool kann bspw. in Eclipse verwendet werden, um die Cloudification nach aktuellem Freigabestatus (B) zu durchsuchen
#---------------------------------------------------------------------------------------------------------------------------

import argparse
from mcp.server.fastmcp import FastMCP
from cloudification.object_repository import ObjectRepository
from cloudification.partner_repository import PartnerRepository
from cloudification.formatter import to_toon

parser = argparse.ArgumentParser(description="MCP FastMCP Server")
parser.add_argument("--port", type=int, default=3124, help="Port für den Server (Default: 3124)")
parser.add_argument("--force-reload", action="store_true", help="Git-Repo beim Start neu clonen")
parser.add_argument("--cloudification-url", type=str, default="https://github.com/SAP/abap-atc-cr-cv-s4hc", help="Cloudification Git-URL")
args = parser.parse_args()

repo = ObjectRepository(repo_url=args.cloudification_url, repo_dir="abap-atc-cr-cv-s4hc", force_reload=args.force_reload)
partner_repo = PartnerRepository()

mcp = FastMCP("Cloudification-Repository", json_response=True, port=args.port, host="0.0.0.0", stateless_http=True)

@mcp.tool()
def search(objectname: str = "*", limit: int = 100, release: str = None, fps: str = None, objecttype: str = None):
    """Suche SAP-Objekte nach Pattern, Limit, Release, FPS, objecttype"""
    results = repo.search_objects(objectname, limit, release=release, fps=fps, objecttype=objecttype)

    needle = objectname.replace("*", "") if objectname != "*" else None
    def matches(obj):
        if needle and needle not in obj.get("tadirObjName", "") and needle not in obj.get("objectKey", ""):
            return False
        if objecttype and obj.get("objectType") != objecttype:
            return False
        return True

    all_results = results + [obj for obj in partner_repo.get_objects() if matches(obj)]
    return {"text": "\n---\n".join(to_toon(obj) for obj in all_results[:limit])}

if __name__ == "__main__":
    repo.init_db()
    mcp.run(transport="streamable-http")
