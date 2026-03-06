# object_repository.py
# Kapselung der DB- und Suchlogik für SAP-Objekte

import os
import json
import sqlite3
from .git_clone import clone_repo

_INSERT_SQL = "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

def _obj_to_row(obj, release, fps):
    return (
        obj.get("tadirObjName", ""),
        obj.get("tadirObject", ""),
        obj.get("objectType", ""),
        obj.get("objectKey", ""),
        obj.get("softwareComponent", ""),
        obj.get("applicationComponent", ""),
        obj.get("state", ""),
        release,
        fps,
        json.dumps(obj.get("successors", [])),
    )


class ObjectRepository:
    DB_PATH = "objects.db"

    def __init__(self, repo_url="https://github.com/SAP/abap-atc-cr-cv-s4hc", repo_dir="abap-atc-cr-cv-s4hc", force_reload=False):
        self.repo_dir = repo_dir
        clone_repo(repo_url, self.repo_dir, force_reload=force_reload)

    @staticmethod
    def _parse_release_fps(fname):
        """Extrahiert Release und FPS aus einem objectReleaseInfo_PCE*.json-Dateinamen."""
        stem = fname.replace("objectReleaseInfo_PCE", "").replace(".json", "")
        parts = stem.split("_")
        if len(parts) == 2:
            return parts[0], parts[1]
        if parts[0] == "Latest":
            return "Latest", None
        return parts[0], None

    def init_db(self):
        db_conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        c = db_conn.cursor()
        src_dir = os.path.join(self.repo_dir, "src")
        json_files = [
            f for f in os.listdir(src_dir)
            if f.startswith("objectReleaseInfo_PCE") and f.endswith(".json")
        ]
        if json_files:
            c.execute("DROP TABLE IF EXISTS objects")
            c.execute("""
                CREATE TABLE objects (
                    tadirObjName TEXT,
                    tadirObject TEXT,
                    objectType TEXT,
                    objectKey TEXT,
                    softwareComponent TEXT,
                    applicationComponent TEXT,
                    state TEXT,
                    release TEXT,
                    fps TEXT,
                    successors TEXT
                )
            """)
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_objects_search "
                "ON objects (tadirObjName, tadirObject, objectType, objectKey, release, fps)"
            )
            for fname in json_files:
                rel, fps = self._parse_release_fps(fname)
                path = os.path.join(src_dir, fname)
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    objs = data["objectReleaseInfo"] if isinstance(data, dict) and "objectReleaseInfo" in data else data
                    print(f"{fname}: {len(objs)} Einträge")
                    rows = []
                    for obj in objs:
                        if not isinstance(obj, dict):
                            print(f"Warnung: Kein Dict in {fname}: {type(obj)}")
                            continue
                        rows.append(_obj_to_row(obj, rel, fps))
                    c.executemany(_INSERT_SQL, rows)
                except Exception as e:
                    print(f"Fehler beim Laden von {fname}: {e}")

        # Klassifizierungsdaten aus objectClassifications_SAP.json einmischen
        path_class = os.path.join(src_dir, "objectClassifications_SAP.json")
        try:
            with open(path_class, encoding="utf-8") as f:
                data = json.load(f)
            objs = data.get("objectClassifications", [])
            print(f"objectClassifications_SAP.json: {len(objs)} Einträge")
            for obj in objs:
                result = c.execute("""
                    UPDATE objects
                    SET state=?, softwareComponent=?, applicationComponent=?, successors=?
                    WHERE tadirObjName=? AND tadirObject=? AND objectType=? AND objectKey=?
                """, (
                    obj.get("state", ""),
                    obj.get("softwareComponent", ""),
                    obj.get("applicationComponent", ""),
                    json.dumps(obj.get("successors", [])),
                    obj.get("tadirObjName", ""),
                    obj.get("tadirObject", ""),
                    obj.get("objectType", ""),
                    obj.get("objectKey", ""),
                ))
                if result.rowcount == 0:
                    c.execute(_INSERT_SQL, _obj_to_row(obj, "Latest", None))
        except Exception as e:
            print(f"Fehler beim Laden von objectClassifications_SAP.json: {e}")

        db_conn.commit()
        for row in c.execute("SELECT release, fps, COUNT(*) FROM objects GROUP BY release, fps"):
            print(f"DB-Release: {row[0]}, FPS: {row[1]}, Anzahl: {row[2]}")
        print("Objektanzahl gesamt:", c.execute("SELECT COUNT(*) FROM objects").fetchone()[0])
        db_conn.close()

    def search_objects(self, pattern: str, limit: int, release=None, fps=None, objecttype=None):
        db_conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        db_conn.row_factory = sqlite3.Row
        c = db_conn.cursor()
        like = pattern.replace("*", "%")
        columns = [
            "tadirObjName", "tadirObject", "objectType", "objectKey",
            "softwareComponent", "applicationComponent", "state", "release", "fps"
        ]
        or_where = " OR ".join([f"{col} LIKE ?" for col in columns])
        params = [like] * len(columns)
        where = f"({or_where})"
        if release:
            where += " AND release=?"
            params.append(release)
        else:
            where += " AND release='Latest'"
        if fps:
            where += " AND fps=?"
            params.append(fps)
        if objecttype:
            where += " AND objectType=?"
            params.append(objecttype)
        params.append(limit)
        rows = c.execute(f"SELECT * FROM objects WHERE {where} LIMIT ?", params).fetchall()
        result = []
        for row in rows:
            obj = dict(row)
            obj["successors"] = json.loads(obj["successors"])
            result.append(obj)
        db_conn.close()
        return result
