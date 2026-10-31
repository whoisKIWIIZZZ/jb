#!/usr/bin/env python3
"""jbmac - 在 Mac 上常驻: 维持到远程 jb dashboard 的 SSH 隧道, 并在任务结束时弹系统通知.

  python3 jbmac.py user@host [-p 22]     前台运行 (通常由 launchd 启动, 见 mac/install.sh)
  python3 jbmac.py --test                只弹一条测试通知
"""
import argparse
import json
import subprocess
import time
import urllib.request

ACTIVE = ("running", "queued")
ST_CN = {"done": "完成", "failed": "失败", "killed": "已终止", "cancelled": "已取消", "lost": "丢失"}


def log(*a):
    print(time.strftime("%F %T"), *a, flush=True)


def notify(title, text):
    def q(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    script = f"display notification {q(text)} with title {q(title)} sound name \"Glass\""
    subprocess.run(["osascript", "-e", script], capture_output=True)


def start_tunnel(a):
    return subprocess.Popen(
        ["ssh", "-N", "-p", str(a.ssh_port), "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes",
         "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3", "-o", "ConnectTimeout=15",
         "-L", f"{a.local_port}:127.0.0.1:{a.remote_port}", a.dest],
        stdin=subprocess.DEVNULL)


def fetch_jobs(a):
    url = f"http://127.0.0.1:{a.local_port}/api/state" + (f"?token={a.token}" if a.token else "")
    with urllib.request.urlopen(url, timeout=8) as r:
        return json.load(r)["jobs"]


def fmt_dur(s):
    s = int(s or 0)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest", nargs="?", help="SSH 目标, 如 user@host 或 ~/.ssh/config 里的别名")
    ap.add_argument("-p", "--ssh-port", type=int, default=22)
    ap.add_argument("--local-port", type=int, default=18765)
    ap.add_argument("--remote-port", type=int, default=18765)
    ap.add_argument("--token", help="jb serve 设置了 --token 时填写")
    ap.add_argument("--poll", type=float, default=10)
    ap.add_argument("--no-tunnel", action="store_true", help="只轮询通知, 不建隧道")
    ap.add_argument("--test", action="store_true", help="弹一条测试通知后退出")
    a = ap.parse_args()
    if a.test:
        notify("[jb] 测试通知", "Mac 本地通知正常")
        return
    if not a.dest and not a.no_tunnel:
        ap.error("需要 SSH 目标 (user@host), 或加 --no-tunnel")

    tunnel = None
    known = None  # id -> status; None 表示还没拿到第一份快照
    while True:
        try:
            jobs = fetch_jobs(a)
        except Exception as e:
            # 连不上才 (重新) 建隧道; 已有别的隧道占着端口时就直接复用它
            if not a.no_tunnel and (tunnel is None or tunnel.poll() is not None):
                log("dashboard unreachable, starting tunnel:", e)
                tunnel = start_tunnel(a)
            time.sleep(a.poll)
            continue
        cur = {j["id"]: j for j in jobs}
        if known is not None:
            for jid, j in cur.items():
                prev = known.get(jid)
                if j["status"] not in ACTIVE and (prev in ACTIVE or prev is None):
                    st = ST_CN.get(j["status"], j["status"])
                    rc = f" rc={j['rc']}" if j.get("rc") not in (None, 0) else ""
                    text = f"{st}{rc} · 用时 {fmt_dur(j.get('elapsed'))}"
                    if j.get("last_line"):
                        text += f"\n{j['last_line'][:120]}"
                    notify(f"[jb] #{jid} {j['name']} {st}", text)
                    log("notified", jid, j["status"])
        known = {jid: j["status"] for jid, j in cur.items()}
        time.sleep(a.poll)


if __name__ == "__main__":
    main()
