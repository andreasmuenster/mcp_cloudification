# git_clone.py
# Modul für das Clonen eines Git-Repos mit GitPython

import os
import stat
import shutil
from git import Repo, GitCommandError

def _force_remove(func, path):
    """Schreibschutz entfernen und Löschen erneut versuchen."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"Fehler beim Entfernen von {path}: {e}")

def clone_repo(repo_url, target_dir, force_reload=False):
    """
    Clont das Repo nach target_dir. Bei force_reload wird das Verzeichnis vorher gelöscht.
    """
    if force_reload and os.path.exists(target_dir):
        print(f"Entferne vorhandenes Repo für force-reload: {target_dir}")
        shutil.rmtree(target_dir, onexc=lambda f, p, _: _force_remove(f, p))
    if not os.path.exists(target_dir):
        try:
            print(f"Cloning {repo_url} nach {target_dir} ...")
            Repo.clone_from(repo_url, target_dir, depth=1)
            print("Clone erfolgreich.")
        except GitCommandError as e:
            print(f"Fehler beim Clonen: {e}")
            print("Verwende lokalen Stand (falls vorhanden).")
    else:
        print("Repo-Verzeichnis existiert, kein Clone nötig.")
