"""Atomic SQLite backup using SQLite's own ``.backup`` API.

    python manage.py backup_db
    python manage.py backup_db --keep 14         # keep last 14 (default 7)
    python manage.py backup_db --dir ./backups   # default DB_DIR/backups

Why this and not ``Copy-Item``/``cp db.sqlite3``: SQLite's online backup
API takes a consistent snapshot even while the DB is being written. A
plain file copy can produce a torn / corrupt backup if Django happens
to be mid-transaction.

After the new snapshot is written, older snapshots beyond ``--keep``
are deleted (newest-first ordering by mtime).

Works identically on the laptop (root project) and on PA (mirrored at
``pythonanywhere/apps/core/management/commands/backup_db.py``). The
``DATABASES['default']['NAME']`` setting points to the right file in
each environment.
"""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a consistent SQLite snapshot via the online backup API."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default="",
                            help="Backup directory (default: <db_dir>/backups).")
        parser.add_argument("--keep", type=int, default=7,
                            help="Retain the N most recent snapshots; older "
                                 "files in the directory are deleted (default 7). "
                                 "Use 0 to keep all.")
        parser.add_argument("--tag", default="",
                            help="Optional filename suffix, e.g. 'pre-dedupe'.")

    def handle(self, *, dir, keep, tag, **opts):
        db_setting = settings.DATABASES.get("default", {})
        if db_setting.get("ENGINE") != "django.db.backends.sqlite3":
            raise CommandError(
                f"backup_db only supports sqlite3; current ENGINE is "
                f"{db_setting.get('ENGINE')!r}"
            )
        db_path = Path(db_setting["NAME"])
        if not db_path.is_file():
            raise CommandError(f"DB file not found: {db_path}")

        out_dir = Path(dir) if dir else db_path.parent / "backups"
        out_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        suffix = f".{tag}" if tag else ""
        out_path = out_dir / f"{db_path.stem}.{ts}{suffix}.sqlite3"

        # Online backup: open both connections, call .backup(). This works
        # even if another process is holding write locks; SQLite copies
        # pages safely under the hood.
        src = sqlite3.connect(str(db_path))
        try:
            dst = sqlite3.connect(str(out_path))
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()

        size_mb = out_path.stat().st_size / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f"backed up {db_path} -> {out_path}  ({size_mb:.2f} MB)"
        ))

        # Prune older snapshots in the same directory. Only touch files
        # matching the stem prefix to avoid clobbering unrelated content
        # (e.g. an old README) the user might keep in the backups dir.
        if keep > 0:
            siblings = sorted(
                (p for p in out_dir.glob(f"{db_path.stem}.*.sqlite3")
                 if p.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            stale = siblings[keep:]
            for p in stale:
                try:
                    p.unlink()
                    self.stdout.write(f"  pruned old snapshot: {p.name}")
                except OSError as exc:
                    self.stderr.write(self.style.WARNING(
                        f"  could not delete {p}: {exc}"
                    ))
