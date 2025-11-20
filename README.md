# Traffic Lights Optimization with Physical AI

This repository provides a Python-based simulation of a camera- and sensor-driven traffic light optimization pipeline designed for deployment on NVIDIA hardware in Malaysia. The project demonstrates how to fuse computer vision detections with ground sensors to drive adaptive signal timing and can be extended to run on NVIDIA Jetson devices using DeepStream/TensorRT.

## Features
- Modular pipeline combining camera detections and loop/IoT sensor inputs.
- Intersection simulation with configurable phases, timing, and detection fidelity.
- NVIDIA-ready inference wrapper to plug in DeepStream/TensorRT models.
- Rule-based controller with hooks for reinforcement learning experimentation in PyTorch.
- CLI entry point to run simulations, log KPIs, and export traces for analysis.

## Quick start
1. Create a Python environment (Python 3.10+ recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run a sample simulation:
   ```bash
   python -m src.main --steps 120 --layout configs/kuala_lumpur_single.yaml
   ```

4. Launch the web portal with login, dashboard, and analytics:
   ```bash
   uvicorn src.web.app:app --reload --port 8000
   ```
   - Default credentials: `admin` / `admin` (override with `PORTAL_ADMIN_PASSWORD`).
   - Access http://localhost:8000 for the login screen, then run simulations and download Omniverse-ready traces from the dashboard.

## NVIDIA integration notes
- `src/vision/nvidia_inference.py` shows how to wrap a TensorRT engine for vehicle and pedestrian detection; replace the stub with an actual DeepStream pipeline when running on Jetson/RTX.
- GPU-based reinforcement learning experiments can be added via `src/control/rl_agent.py`.

## Repository structure
- `configs/`: YAML layouts for intersections and corridor networks.
- `src/`: Python package implementing simulation, control, and vision modules.
- `tests/`: Basic tests for core components (extend as needed).

## Corridor synchronization and digital twin exports
- Use `configs/kuala_lumpur_corridor.yaml` to simulate two synchronized intersections with green-wave offsets.
- The `src/simulation/network.py` module runs multi-node simulations via `run_network_simulation` and the `CoordinatedSignalManager`.
- Export Omniverse-ready synthetic data with `export_omniverse_synthetic_data` from `src/simulation/omniverse.py` using the histories of the simulated intersections.

## License
Distributed under the MIT License.
