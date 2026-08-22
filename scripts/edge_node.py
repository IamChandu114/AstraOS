import os
import psutil
import platform
import time
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="AstraOS Edge Node")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NODE_ID = os.getenv("ASTRAOS_EDGE_NODE_ID", "astra-edge-01")
START_TIME = time.time()

class NetworkTracker:
    def __init__(self):
        self.last_time = time.time()
        self.last_net = psutil.net_io_counters()

    def get_bps(self):
        now = time.time()
        current_net = psutil.net_io_counters()
        
        time_diff = now - self.last_time
        if time_diff <= 0:
            time_diff = 1.0
            
        rx_bps = (current_net.bytes_recv - self.last_net.bytes_recv) / time_diff
        tx_bps = (current_net.bytes_sent - self.last_net.bytes_sent) / time_diff
        
        self.last_time = now
        self.last_net = current_net
        
        return rx_bps, tx_bps

net_tracker = NetworkTracker()

@app.get("/telemetry")
async def get_telemetry():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    rx_bps, tx_bps = net_tracker.get_bps()
    
    return {
        "node_id": NODE_ID,
        "timestamp": time.time(),
        "cpu_percent": cpu,
        "memory_percent": mem,
        "network_rx_bps": rx_bps,
        "network_tx_bps": tx_bps,
        "hostname": platform.node(),
        "os": platform.system(),
        "uptime_seconds": time.time() - START_TIME,
        "health": "LIVE"
    }

if __name__ == "__main__":
    # Prime CPU percent
    psutil.cpu_percent(interval=None)
    port = int(os.getenv("PORT", "8080"))
    print(f"Starting AstraOS Edge Node {NODE_ID} on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
