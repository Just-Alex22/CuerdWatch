import psutil
from datetime import datetime
import platform

def get_system_stats():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    
    return {
        'cpu_perc': psutil.cpu_percent(),
        'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        'mem_perc': mem.percent,
        'mem_used': mem.used / (1024**3),
        'mem_total': mem.total / (1024**3),
        'disk_perc': disk.percent,
        'disk_used': disk.used / (1024**3),
        'disk_total': disk.total / (1024**3),
        'uptime': f"{uptime.days}d {uptime.seconds//3600}h { (uptime.seconds//60)%60 }m",
        'cores': psutil.cpu_count(logical=True),
        'os': platform.system()
    }

def get_processes_info(view_mode, current_user, search_text=""):
    proc_list = []
    search_text = search_text.lower()
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'status']):
        try:
            p = proc.info
            user = p['username'] or "N/A"
            if view_mode == "my" and user != current_user: continue
            if view_mode == "non-root" and user.lower() in ["root", "0"]: continue
            if search_text and search_text not in p['name'].lower(): continue
            proc_list.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied): continue
    return proc_list