from __future__ import annotations

import os
import secrets
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.control.policy import DemandResponsiveController
from src.simulation.omniverse import export_omniverse_synthetic_data
from src.simulation.simulator import run_simulation
from src.utils.config import LayoutConfig, load_layout


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_DIR = BASE_DIR.parent.parent / "configs"


@dataclass
class SimulationRun:
    id: str
    layout: str
    steps: int
    arrival_intensity: float
    crossing_rate: float
    created_at: datetime
    metrics: Dict[str, float]
    history: List[dict] = field(default_factory=list)
    omniverse_path: Optional[Path] = None


class SimulationStore:
    def __init__(self, config_dir: Path = DEFAULT_CONFIG_DIR) -> None:
        self.config_dir = config_dir
        self.runs: Dict[str, SimulationRun] = {}
        self.layout_index = self._discover_layouts()

    def _discover_layouts(self) -> Dict[str, Path]:
        layouts: Dict[str, Path] = {}
        for path in self.config_dir.glob("*.yaml"):
            layout = load_layout(path)
            layouts[layout.id] = path
        return layouts

    def available_layouts(self) -> List[LayoutConfig]:
        return [load_layout(path) for path in self.layout_index.values()]

    def _ensure_layout(self, layout_id: str) -> Path:
        if layout_id in self.layout_index:
            return self.layout_index[layout_id]
        candidate = self.config_dir / layout_id
        if candidate.exists():
            layout = load_layout(candidate)
            self.layout_index[layout.id] = candidate
            return candidate
        raise HTTPException(status_code=404, detail=f"Layout {layout_id} not found")

    @staticmethod
    def _summarize(history: List[dict]) -> Dict[str, float]:
        if not history:
            return {"avg_queue": 0.0, "max_queue": 0.0, "avg_pedestrians": 0.0}
        queue_samples: List[int] = []
        ped_samples: List[int] = []
        for sample in history:
            queue_samples.extend(sample.get("queues", {}).values())
            ped_samples.extend(sample.get("pedestrians", {}).values())
        return {
            "avg_queue": statistics.fmean(queue_samples) if queue_samples else 0.0,
            "max_queue": max(queue_samples) if queue_samples else 0.0,
            "avg_pedestrians": statistics.fmean(ped_samples) if ped_samples else 0.0,
        }

    def run(self, layout_id: str, steps: int, arrival_intensity: float, crossing_rate: float) -> SimulationRun:
        layout_path = self._ensure_layout(layout_id)
        layout = load_layout(layout_path)
        controller = DemandResponsiveController()
        intersection = run_simulation(
            layout=layout,
            controller=controller,
            steps=steps,
            arrival_intensity=arrival_intensity,
            crossing_rate=crossing_rate,
        )
        metrics = self._summarize(intersection.history)
        run_id = uuid.uuid4().hex
        run = SimulationRun(
            id=run_id,
            layout=layout.id,
            steps=steps,
            arrival_intensity=arrival_intensity,
            crossing_rate=crossing_rate,
            created_at=datetime.utcnow(),
            metrics=metrics,
            history=intersection.history,
        )
        self.runs[run_id] = run
        return run

    def analytics(self) -> Dict[str, float]:
        if not self.runs:
            return {"runs": 0, "avg_queue": 0.0, "max_queue": 0.0, "avg_pedestrians": 0.0}
        avg_queues = [run.metrics["avg_queue"] for run in self.runs.values()]
        max_queues = [run.metrics["max_queue"] for run in self.runs.values()]
        avg_peds = [run.metrics["avg_pedestrians"] for run in self.runs.values()]
        return {
            "runs": len(self.runs),
            "avg_queue": statistics.fmean(avg_queues) if avg_queues else 0.0,
            "max_queue": max(max_queues) if max_queues else 0.0,
            "avg_pedestrians": statistics.fmean(avg_peds) if avg_peds else 0.0,
        }

    def export(self, run_id: str, output_dir: Path | None = None) -> Path:
        if run_id not in self.runs:
            raise HTTPException(status_code=404, detail="Run not found")
        run = self.runs[run_id]
        output_dir = output_dir or BASE_DIR.parent.parent / "artifacts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{run_id}_omniverse.json"
        run.omniverse_path = export_omniverse_synthetic_data(
            intersections=[self._history_to_intersection(run)], output_path=output_path
        )
        return output_path

    @staticmethod
    def _history_to_intersection(run: SimulationRun):
        from src.simulation.entities import IntersectionState, LaneState, PhaseState

        lanes = {}
        if run.history:
            sample_queues = run.history[0].get("queues", {})
            lanes = {lane_id: LaneState(id=lane_id, queue=0) for lane_id in sample_queues}
        phases = [PhaseState(name="phase", lanes=list(lanes.keys()), min_green=5, max_green=5)]
        intersection = IntersectionState(layout_id=run.layout, phases=phases, lanes=lanes)
        intersection.history = run.history
        return intersection


def create_app(config_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Traffic Light Simulation Portal", version="0.2.0")
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    app.add_middleware(SessionMiddleware, secret_key=os.getenv("PORTAL_SECRET", "change-me"))

    store = SimulationStore(config_dir=config_dir or DEFAULT_CONFIG_DIR)
    users = {"admin": os.getenv("PORTAL_ADMIN_PASSWORD", "admin")}

    def require_user(request: Request) -> str:
        if request.session.get("user") not in users:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return request.session["user"]

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        if request.session.get("user"):
            return RedirectResponse(url="/dashboard", status_code=302)
        return templates.TemplateResponse("login.html", {"request": request, "error": None})

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        return templates.TemplateResponse("login.html", {"request": request, "error": None})

    @app.post("/login")
    async def login(request: Request, username: str = Form(...), password: str = Form(...)):
        if username not in users or not secrets.compare_digest(users[username], password):
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Invalid credentials"}, status_code=401
            )
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=302)

    @app.get("/logout")
    async def logout(request: Request):
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request, user: str = Depends(require_user)):
        analytics = store.analytics()
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "layouts": store.available_layouts(),
                "runs": list(store.runs.values()),
                "analytics": analytics,
            },
        )

    @app.post("/api/simulations")
    async def launch_simulation(
        user: str = Depends(require_user),
        layout: str = Form(...),
        steps: int = Form(120),
        arrival_intensity: float = Form(0.7),
        crossing_rate: float = Form(0.2),
    ):
        run = store.run(layout_id=layout, steps=steps, arrival_intensity=arrival_intensity, crossing_rate=crossing_rate)
        return JSONResponse(run.__dict__)

    @app.get("/api/analytics")
    async def api_analytics(user: str = Depends(require_user)):
        return store.analytics()

    @app.get("/api/simulations/{run_id}/omniverse")
    async def download_omniverse(run_id: str, user: str = Depends(require_user)):
        path = store.export(run_id)
        return FileResponse(path, media_type="application/json", filename=path.name)

    @app.get("/health")
    async def healthcheck():
        return {"status": "ok"}

    return app


app = create_app()
