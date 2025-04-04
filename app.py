from flask import Flask, render_template
import subprocess
import os
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

REPO_MAP = {
    "/app/code/big-ann-stat": "Big-ANN-Benchmarks",
    "/app/code/CC-HNSW": "CC-HNSW",
    "/app/code/CANDY-Benchmark": "CANDOR-Bench",
    "/app/code/Parlay-HNSW": "Parlay-HNSW"
    "/app/code/stagewise-gt-tools": "GT-Tools"
}
TARGET_REPOS = list(REPO_MAP.keys())

TIME_RANGES = {
    "1 Day": lambda: datetime.utcnow() - timedelta(days=1),
    "7 Days": lambda: datetime.utcnow() - timedelta(days=7),
    "1 Month": lambda: datetime.utcnow() - timedelta(days=30),
    "1 Year": lambda: datetime.utcnow() - timedelta(days=365),
}

# Global variables to store stats and last updated time
stats_data = {}
overall_stats_data = {}
last_updated = None

def get_git_stats(repo_path, since=None, file_path=None):
    try:
        os.chdir(repo_path)
        cmd = ['git', 'log', '--author=1071307515@qq.com', '--pretty=tformat:%H', '--numstat']
        if since:
            cmd.append(f'--since={since.strftime("%Y-%m-%d %H:%M:%S")}')
        if file_path:  # 如果指定了文件，只统计该文件
            cmd.append('--')
            cmd.append(file_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        insertions, deletions, commits = 0, 0, 0
        current_commit = None
        
        for line in result.stdout.splitlines():
            if line.strip() and len(line) == 40 and all(c in '0123456789abcdef' for c in line.lower()):
                commits += 1
                current_commit = line
            elif line.strip() and current_commit:
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    insertions += int(parts[0])
                    deletions += int(parts[1])

        return {
            "commits": commits,
            "insertions": insertions,
            "deletions": deletions,
            "total_changes": insertions + deletions
        }
    except subprocess.CalledProcessError as e:
        print(f"❌ Error processing {repo_path}: {e}")
        return {"commits": 0, "insertions": 0, "deletions": 0, "total_changes": 0, "error": str(e)}
    except Exception as e:
        print(f"❌ Error processing {repo_path}: {e}")
        return {"commits": 0, "insertions": 0, "deletions": 0, "total_changes": 0, "error": str(e)}
    finally:
        os.chdir(os.path.expanduser("~"))

def update_stats():
    global stats_data, overall_stats_data, last_updated
    while True:
        stats = {}
        overall_stats = {
            "1 Day": {"commits": 0, "insertions": 0, "deletions": 0, "total_changes": 0},
            "7 Days": {"commits": 0, "insertions": 0, "deletions": 0, "total_changes": 0},
            "1 Month": {"commits": 0, "insertions": 0, "deletions": 0, "total_changes": 0},
            "1 Year": {"commits": 0, "insertions": 0, "deletions": 0, "total_changes": 0}
        }

        for repo in TARGET_REPOS:
            display_name = REPO_MAP[repo]
            if not os.path.exists(repo) or not os.path.exists(os.path.join(repo, ".git")):
                stats[display_name] = {range_name: {"error": "Not a valid Git repository"} for range_name in TIME_RANGES}
                continue
            
            stats[display_name] = {}
            for range_name, since_func in TIME_RANGES.items():
                # 只对 Parlay-HNSW 统计 algorithms/bench/benchmark.C，其他统计所有文件
                file_path = "algorithms/bench/benchmark.C" if repo == "/app/code/Parlay-HNSW" else None
                range_stats = get_git_stats(repo, since_func(), file_path=file_path)
                stats[display_name][range_name] = range_stats
                for key in ["commits", "insertions", "deletions", "total_changes"]:
                    overall_stats[range_name][key] += range_stats[key]

        # Update global data and timestamp
        stats_data = stats
        overall_stats_data = overall_stats
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"📊 Stats updated at {last_updated}")
        time.sleep(3600)  # Update every hour

@app.route("/")
def index():
    return render_template("index.html", stats=stats_data, overall_stats=overall_stats_data, last_updated=last_updated)

# Start the stats update thread
threading.Thread(target=update_stats, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)