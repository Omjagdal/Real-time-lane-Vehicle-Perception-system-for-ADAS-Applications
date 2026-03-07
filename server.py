"""
server.py
---------
FastAPI backend for the ADAS React UI.

Endpoints
---------
POST  /api/upload          – Upload a video file, returns job_id
GET   /api/process/{id}    – SSE stream: live frame stats + progress
GET   /api/frame/{id}      – Latest annotated JPEG frame
GET   /api/download/{id}   – Download the annotated .mp4
GET   /api/jobs            – List all jobs
DELETE /api/jobs/{id}      – Delete a job

Run:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
    JSONResponse,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="ADAS Perception API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Storage directories
# ---------------------------------------------------------------------------

JOBS_DIR = Path("jobs")
JOBS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# In-memory job registry
# ---------------------------------------------------------------------------

jobs: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# ADAS pipeline (lazy load once)
# ---------------------------------------------------------------------------

_pipeline_cache = {}

def _get_pipeline(conf: float = 0.4, device: str = "cpu",
                  ego_speed: float = 60.0):
    key = (conf, device, ego_speed)
    if key not in _pipeline_cache:
        from src.preprocessing     import TARGET_HEIGHT
        from src.lane_detection    import LaneDetector
        from src.vehicle_detection import VehicleDetector
        from src.tracker           import IoUTracker
        from src.distance          import DistanceEstimator
        from src.speed             import SpeedEstimator
        from src.fcw               import FCWEngine

        _pipeline_cache[key] = {
            "lane_detector": LaneDetector(),
            "detector"     : VehicleDetector(conf=conf, device=device),
            "tracker"      : IoUTracker(),
            "dist_est"     : DistanceEstimator(frame_height=TARGET_HEIGHT),
            "speed_est"    : SpeedEstimator(fps=30.0),
            "fcw_engine"   : FCWEngine(ego_speed_kmh=ego_speed),
        }
    return _pipeline_cache[key]

# ---------------------------------------------------------------------------
# Core per-frame processing
# ---------------------------------------------------------------------------

def _run_frame(frame, pipeline, ego_speed):
    from src.preprocessing import preprocess_for_lane, preprocess_for_detection, resize_frame
    from src.visualization import draw_lanes, draw_vehicles, draw_fcw_banner, draw_hud
    from src.fcw           import FCWEngine, AlertLevel

    edge_img  = preprocess_for_lane(frame)
    prep      = preprocess_for_detection(frame)

    left_lane, right_lane = pipeline["lane_detector"].detect(
        edge_img, frame.shape[0], frame.shape[1])

    detections = pipeline["detector"].detect(prep)
    tracks     = pipeline["tracker"].update(detections)
    distances  = pipeline["dist_est"].estimate_all(tracks)
    speeds     = pipeline["speed_est"].update(tracks, distances)
    fcw_res    = pipeline["fcw_engine"].evaluate(tracks, distances, speeds,
                                                  ego_speed=ego_speed)
    critical   = FCWEngine.most_critical(fcw_res)

    out = resize_frame(frame)
    out = draw_lanes(out, left_lane, right_lane)
    out = draw_vehicles(out, tracks, distances, speeds, fcw_res)
    out = draw_fcw_banner(out, critical)
    out = draw_hud(out, fps=0.0, num_tracks=len(tracks),
                   ego_speed_kmh=ego_speed)

    # Collect stats
    brake_count   = sum(1 for r in fcw_res.values()
                        if r.alert == AlertLevel.BRAKE)
    caution_count = sum(1 for r in fcw_res.values()
                        if r.alert == AlertLevel.CAUTION)

    return out, {
        "num_vehicles" : len(tracks),
        "brake_events" : brake_count,
        "caution_events": caution_count,
        "distances"    : {str(t.track_id): round(distances.get(t.track_id, 0), 1)
                          for t in tracks},
        "speeds"       : {str(t.track_id): round(speeds.get(t.track_id, 0), 1)
                          for t in tracks},
    }

# ---------------------------------------------------------------------------
# Background processing task
# ---------------------------------------------------------------------------

def _process_video(job_id: str, input_path: str, output_path: str,
                   conf: float, device: str, ego_speed: float,
                   max_frames: int):
    job = jobs[job_id]
    job["status"] = "processing"

    try:
        pipeline = _get_pipeline(conf, device, ego_speed)

        cap = cv2.VideoCapture(input_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps   = cap.get(cv2.CAP_PROP_FPS) or 30.0
        pipeline["speed_est"]._fps = fps

        from src.preprocessing import TARGET_WIDTH, TARGET_HEIGHT
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps,
                                 (TARGET_WIDTH, TARGET_HEIGHT))

        frame_idx   = 0
        total_brake = 0
        total_caution = 0
        frames_to_proc = min(max_frames, total) if total > 0 else max_frames

        job["total_frames"]   = frames_to_proc
        job["fps_source"]     = fps

        t_start = time.perf_counter()

        while frame_idx < frames_to_proc:
            ret, frame = cap.read()
            if not ret:
                break

            t0 = time.perf_counter()
            annotated, stats = _run_frame(frame, pipeline, ego_speed)
            elapsed_frame = time.perf_counter() - t0

            writer.write(annotated)

            total_brake   += stats["brake_events"]
            total_caution += stats["caution_events"]

            # Save latest JPEG preview
            preview_path = str(JOBS_DIR / job_id / "preview.jpg")
            cv2.imwrite(preview_path, annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])

            # Update job state (read by SSE stream)
            job["frame"]          = frame_idx + 1
            job["fps_live"]       = round(1.0 / max(elapsed_frame, 0.001), 1)
            job["num_vehicles"]   = stats["num_vehicles"]
            job["brake_events"]   = total_brake
            job["caution_events"] = total_caution
            job["distances"]      = stats["distances"]
            job["speeds"]         = stats["speeds"]

            frame_idx += 1

        cap.release()
        writer.release()

        elapsed = time.perf_counter() - t_start
        job["status"]         = "done"
        job["elapsed"]        = round(elapsed, 2)
        job["avg_fps"]        = round(frame_idx / max(elapsed, 0.01), 1)
        job["output_path"]    = output_path

    except Exception as e:
        job["status"] = "error"
        job["error"]  = str(e)
        raise

# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file       : UploadFile = File(...),
    conf       : float = 0.4,
    device     : str   = "cpu",
    ego_speed  : float = 60.0,
    max_frames : int   = 500,
):
    job_id   = str(uuid.uuid4())
    job_dir  = JOBS_DIR / job_id
    job_dir.mkdir(parents=True)

    input_path  = str(job_dir / "input.mp4")
    output_path = str(job_dir / "annotated.mp4")

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    jobs[job_id] = {
        "job_id"       : job_id,
        "filename"     : file.filename,
        "status"       : "queued",
        "frame"        : 0,
        "total_frames" : 0,
        "fps_live"     : 0.0,
        "avg_fps"      : 0.0,
        "num_vehicles" : 0,
        "brake_events" : 0,
        "caution_events": 0,
        "elapsed"      : 0.0,
        "distances"    : {},
        "speeds"       : {},
        "created_at"   : time.time(),
        "conf"         : conf,
        "ego_speed"    : ego_speed,
        "device"       : device,
    }

    background_tasks.add_task(
        _process_video,
        job_id, input_path, output_path,
        conf, device, ego_speed, max_frames,
    )

    return {"job_id": job_id}


@app.get("/api/process/{job_id}")
async def stream_progress(job_id: str):
    """Server-Sent Events stream of processing progress."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        while True:
            job = jobs.get(job_id, {})
            payload = {
                "status"        : job.get("status"),
                "frame"         : job.get("frame", 0),
                "total_frames"  : job.get("total_frames", 0),
                "fps_live"      : job.get("fps_live", 0.0),
                "num_vehicles"  : job.get("num_vehicles", 0),
                "brake_events"  : job.get("brake_events", 0),
                "caution_events": job.get("caution_events", 0),
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if job.get("status") in ("done", "error"):
                break
            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/frame/{job_id}")
async def get_preview_frame(job_id: str):
    """Return latest annotated JPEG frame."""
    preview = JOBS_DIR / job_id / "preview.jpg"
    if not preview.exists():
        raise HTTPException(status_code=404, detail="No frame yet")
    return FileResponse(str(preview), media_type="image/jpeg")


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/jobs")
async def list_jobs():
    return list(jobs.values())


@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail="Job not complete")
    path = job.get("output_path", "")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Output file missing")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"adas_{job_id[:8]}.mp4",
    )


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job_dir = JOBS_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    del jobs[job_id]
    return {"deleted": job_id}


@app.get("/api/health")
async def health():
    return {"status": "ok", "jobs": len(jobs)}
