"""Write docs/api/openapi.json from the FastAPI app. Usage (from backend/): uv run python scripts/export_openapi.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pixactions_api.config import Settings
from pixactions_api.main import create_app

spec = create_app(Settings(_env_file=None, public_api_url="https://api.pixactions.app")).openapi()
out = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {out}")
