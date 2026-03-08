import argparse
import os
import subprocess
import sys
from pathlib import Path


def _env_flag(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def main() -> int:
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent
    default_frontend_dir = repo_root / "mesh-generator"

    parser = argparse.ArgumentParser(
        description="Build mesh-generator frontend and run mesh-backend in one command.",
    )
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", default=os.getenv("PORT", "8000"))
    parser.add_argument(
        "--frontend-dir",
        default=os.getenv("MESH_FRONTEND_DIR", str(default_frontend_dir)),
        help="Path to mesh-generator frontend repository.",
    )
    parser.add_argument(
        "--dist-dir",
        default=os.getenv("FRONTEND_DIST_DIR", ""),
        help="Frontend dist directory. Defaults to <frontend-dir>/dist.",
    )
    parser.add_argument(
        "--npm-bin",
        default=os.getenv("NPM_BIN", "npm"),
        help="npm executable to use for frontend build.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        default=_env_flag("SKIP_FRONTEND_BUILD", False),
        help="Skip frontend build and use existing dist output.",
    )
    args = parser.parse_args()

    frontend_dir = Path(args.frontend_dir).expanduser().resolve()
    if not frontend_dir.is_dir():
        raise SystemExit(f"Frontend directory not found: {frontend_dir}")

    dist_dir = Path(args.dist_dir).expanduser().resolve() if args.dist_dir else (frontend_dir / "dist").resolve()

    if not args.skip_build:
        print(f"[mesh-web] Building frontend in {frontend_dir}")
        subprocess.run([args.npm_bin, "run", "build"], cwd=frontend_dir, check=True)

    env = os.environ.copy()
    env["FRONTEND_DIST_DIR"] = str(dist_dir)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        str(args.host),
        "--port",
        str(args.port),
    ]
    print(f"[mesh-web] Starting backend with FRONTEND_DIST_DIR={dist_dir}")
    return subprocess.call(cmd, cwd=backend_dir, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
