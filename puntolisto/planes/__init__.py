"""Paquete de planes: carga y expone todas las constantes de puntolisto/planes.py."""
from pathlib import Path

_archivo_planes = Path(__file__).resolve().parent.parent / "planes.py"
exec(compile(_archivo_planes.read_text(encoding="utf-8"), str(_archivo_planes), "exec"), globals())
