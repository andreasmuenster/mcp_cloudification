# partner_repository.py
# Lädt alle objectClassifications_*.json aus src/partner und stellt sie als Liste bereit

import os
import json

class PartnerRepository:
    def __init__(self, partner_dir="abap-atc-cr-cv-s4hc/src/partner"):
        self.partner_dir = partner_dir
        self.objects = []
        self.load_partner_objects()

    def load_partner_objects(self):
        if not os.path.isdir(self.partner_dir):
            print(f"Partner-Verzeichnis nicht gefunden, überspringe: {self.partner_dir}")
            return
        for fname in os.listdir(self.partner_dir):
            if fname.startswith("objectClassifications_") and fname.endswith(".json"):
                path = os.path.join(self.partner_dir, fname)
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                        # Format: {"formatVersion": "2", "objectClassifications": [...]}
                        objs = data.get("objectClassifications", [])
                        self.objects.extend(objs)
                except Exception as e:
                    print(f"Fehler beim Laden von {fname}: {e}")

    def get_objects(self):
        return self.objects
