"""
MBO Project Leader - 연도별 프로젝트 목표 관리 프로그램
======================================================
순수 데스크톱 애플리케이션 (tkinter 기반)
웹 서버 없이 독립 실행되며, SQLite로 로컬 저장합니다.
추가 패키지 설치 없이 Python만으로 실행됩니다.
"""

<<<<<<< HEAD
__version__ = ""
=======
__version__ = "2026.03.04.4"
>>>>>>> 8329dde (v2026.03.04.4 - 업데이트 수정)

import os
import sys
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
import calendar
import threading
import webbrowser
from urllib.request import urlopen, Request
from urllib.error import URLError

# ============================================================
# Auto-Updater (GitHub Releases)
# ============================================================
# TODO: 아래 값을 실제 GitHub 저장소로 변경하세요
GITHUB_OWNER = "HyeonheeKIM"   # ← GitHub 사용자명
GITHUB_REPO  = "MBO-Project-Leader"     # ← 저장소 이름


def _parse_version(v: str):
    """'1.2.3' → (1, 2, 3) 튜플로 변환"""
    return tuple(int(x) for x in v.strip().lstrip("v").split("."))


def check_update_async(parent_window):
    """백그라운드 스레드에서 최신 버전 확인 → 새 버전 있으면 다이얼로그 표시"""
    def _worker():
        try:
            url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            req = Request(url, headers={"Accept": "application/vnd.github.v3+json",
                                        "User-Agent": "MBO-Project-Leader-Updater"})
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            latest = data.get("tag_name", "0.0.0")
            if _parse_version(latest) > _parse_version(__version__):
                body = data.get("body", "")[:300]
                # assets에서 .exe 다운로드 URL 찾기
                exe_url = ""
                for asset in data.get("assets", []):
                    if asset.get("name", "").lower().endswith(".exe"):
                        exe_url = asset.get("browser_download_url", "")
                        break
                fallback_url = data.get("html_url", "")
                parent_window.after(0, lambda: _show_update_dialog(
                    parent_window, latest, exe_url, fallback_url, body))
        except (URLError, Exception):
            pass   # 네트워크 오류 시 조용히 무시

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _download_and_launch(parent, exe_url, version):
    """EXE 다운로드 → 현재 프로그램 종료 → 새 EXE 실행"""
    import subprocess

    # 진행 표시 다이얼로그
    dlg = tk.Toplevel(parent)
    dlg.title("업데이트 중...")
    dlg.geometry("380x140")
    dlg.configure(bg="#f0f2fc")
    dlg.transient(parent)
    dlg.grab_set()
    dlg.resizable(False, False)
    dlg.protocol("WM_DELETE_WINDOW", lambda: None)  # 닫기 방지

    tk.Label(dlg, text=f"v{version} 다운로드 중...", font=("맑은 고딕", 11, "bold"),
             bg="#f0f2fc", fg="#1c1e3a").pack(pady=(20, 8))
    prog_var = tk.DoubleVar(value=0)
    prog_bar = ttk.Progressbar(dlg, variable=prog_var, maximum=100, length=320)
    prog_bar.pack(padx=20)
    status_lbl = tk.Label(dlg, text="연결 중...", font=("맑은 고딕", 9), bg="#f0f2fc", fg="#6b7280")
    status_lbl.pack(pady=(4, 0))

    def _update_ui(func):
        """메인 스레드에서 안전하게 UI 업데이트"""
        try:
            parent.after(0, func)
        except Exception:
            pass

    def _download():
        try:
            # 다운로드 위치 결정
            if getattr(sys, 'frozen', False):
                dest_dir = os.path.dirname(sys.executable)
                old_exe = sys.executable
                old_name = os.path.basename(old_exe)
            else:
                dest_dir = os.path.dirname(os.path.abspath(__file__))
                old_exe = None
                old_name = None

            # 임시 파일명으로 다운로드 (실행 중인 EXE와 충돌 방지)
            temp_name = f"MBO_Project_Leader_v{version}_new.exe"
            dest_path = os.path.join(dest_dir, temp_name)

            req = Request(exe_url, headers={"User-Agent": "MBO-Project-Leader-Updater"})
            resp = urlopen(req, timeout=120)
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536

            with open(dest_path, 'wb') as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded / total * 100
                        mb = downloaded / 1024 / 1024
                        tmb = total / 1024 / 1024
                        _update_ui(lambda p=pct: prog_var.set(p))
                        _update_ui(lambda m=mb, t=tmb: status_lbl.configure(
                            text=f"{m:.1f} MB / {t:.1f} MB"))

            _update_ui(lambda: prog_var.set(100))
            _update_ui(lambda: status_lbl.configure(text="다운로드 완료! 재시작 준비 중..."))

            # 다운로드 파일 크기 확인
            if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 1024:
                _update_ui(lambda: status_lbl.configure(text="오류: 다운로드 파일이 올바르지 않습니다."))
                _update_ui(lambda: dlg.after(3000, dlg.destroy))
                return

            if old_exe:
                # EXE 모드: 배치파일로 교체 후 실행
                # 현재 EXE를 .old로 rename → 새 파일을 원래 이름으로 rename → 실행
                bat_path = os.path.join(dest_dir, "_update.bat")
                old_backup = old_exe + ".old"
                with open(bat_path, 'w', encoding='utf-8') as bf:
                    bf.write('@echo off\n')
                    bf.write('chcp 65001 >nul\n')
                    bf.write('echo 업데이트 중... 잠시 기다려주세요.\n')
                    bf.write(f'echo 이전 버전 백업 중...\n')
                    bf.write(':wait_loop\n')
                    bf.write(f'timeout /t 1 /nobreak >nul\n')
                    bf.write(f'ren "{old_exe}" "{os.path.basename(old_backup)}" 2>nul\n')
                    bf.write(f'if exist "{old_exe}" goto wait_loop\n')
                    bf.write(f'echo 새 버전 적용 중...\n')
                    bf.write(f'copy /y "{dest_path}" "{old_exe}" >nul\n')
                    bf.write(f'if errorlevel 1 (\n')
                    bf.write(f'    echo 업데이트 실패. 이전 버전을 복원합니다.\n')
                    bf.write(f'    ren "{old_backup}" "{old_name}" 2>nul\n')
                    bf.write(f'    pause\n')
                    bf.write(f'    exit /b 1\n')
                    bf.write(f')\n')
                    bf.write(f'del "{dest_path}" 2>nul\n')
                    bf.write(f'del "{old_backup}" 2>nul\n')
                    bf.write(f'echo 업데이트 완료! 프로그램을 시작합니다.\n')
                    bf.write(f'start "" "{old_exe}"\n')
                    bf.write(f'del "%~f0" 2>nul\n')

                # 배치 실행 후 앱 종료 (1초 유예)
                subprocess.Popen(["cmd", "/c", bat_path],
                                 creationflags=0x08000000)  # CREATE_NO_WINDOW
                import time
                time.sleep(1)
                _update_ui(lambda: parent.destroy())
                os._exit(0)  # 강제 종료하여 EXE 파일 잠금 해제
            else:
                # 개발 모드: 새 EXE 바로 실행
                subprocess.Popen([dest_path])
                _update_ui(lambda: parent.destroy())

        except Exception as ex:
            _update_ui(lambda: status_lbl.configure(text=f"오류: {ex}"))
            _update_ui(lambda: dlg.after(5000, dlg.destroy))

    t = threading.Thread(target=_download, daemon=True)
    t.start()


def _show_update_dialog(parent, version, exe_url, fallback_url, notes):
    """새 버전 안내 다이얼로그 — EXE 자동 다운로드 & 실행"""
    if exe_url:
        msg = (f"새 버전이 있습니다!\n\n"
               f"현재: v{__version__}  →  최신: {version}\n\n"
               f"{notes}\n\n"
               f"자동으로 다운로드하고 실행할까요?")
        if messagebox.askyesno("업데이트 알림", msg, parent=parent):
            _download_and_launch(parent, exe_url, version)
    else:
        msg = (f"새 버전이 있습니다!\n\n"
               f"현재: v{__version__}  →  최신: {version}\n\n"
               f"{notes}\n\n"
               f"다운로드 페이지를 열까요?")
        if messagebox.askyesno("업데이트 알림", msg, parent=parent):
            webbrowser.open(fallback_url)

# ============================================================
# Database
# ============================================================
# PyInstaller --onefile 시 __file__은 임시폴더를 가리키므로
# EXE 위치 기준으로 DB를 저장해야 데이터가 유지됩니다.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mbo_project_leader.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS years (
            year INTEGER PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            year        INTEGER NOT NULL,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            kpi         TEXT DEFAULT '',
            weight      REAL DEFAULT 0,
            priority    INTEGER DEFAULT 1,
            difficulty  TEXT DEFAULT '보통',
            status      TEXT DEFAULT '대기',
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (year) REFERENCES years(year) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS monthly_plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL,
            month       INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
            milestone   TEXT DEFAULT '',
            target      TEXT DEFAULT '',
            status      TEXT DEFAULT '미완료',
            note        TEXT DEFAULT '',
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            UNIQUE(project_id, month)
        );
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL,
            task_date   TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            is_done     INTEGER DEFAULT 0,
            priority    INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
    """)
    now_year = datetime.now().year
    conn.execute("INSERT OR IGNORE INTO years (year) VALUES (?)", (now_year,))
    # Migration: add difficulty column if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()]
    if "difficulty" not in cols:
        conn.execute("ALTER TABLE projects ADD COLUMN difficulty TEXT DEFAULT '보통'")
    conn.commit()
    conn.close()


# ============================================================
# Color Theme (Dark mode)
# ============================================================
class Theme:
    # ── Liquid Glass  (light frosted-glass palette) ──
    BG            = "#e4e8f7"     # main area — soft lavender mist
    BG_DARK       = "#cdd3ec"     # sidebar  — deeper frosted glass
    BG_CARD       = "#f0f2fc"     # cards    — near-white glass panel
    BG_CARD_HOVER = "#e2e5f4"     # hover / alt rows
    BG_INPUT      = "#ffffff"     # inputs   — clear glass
    BORDER        = "#bcc2dd"     # glass edge highlight
    ACCENT_BLUE   = "#4a8afe"
    ACCENT_CYAN   = "#06b6d4"
    ACCENT_PURPLE = "#7c5cf6"
    ACCENT_GREEN  = "#10b981"
    ACCENT_YELLOW = "#f59e0b"
    ACCENT_RED    = "#ef4444"
    ACCENT_PINK   = "#ec4899"
    TEXT          = "#1c1e3a"     # primary — deep navy
    TEXT_DIM      = "#5c5f85"     # secondary
    TEXT_DARK     = "#8b8eb3"     # tertiary
    WHITE         = "#ffffff"

    # Milestone colors
    MILESTONE_COLORS = {
        "요구 분석":   "#6366f1",
        "기능 개발":   "#06b6d4",
        "검증":       "#f59e0b",
        "PILOT":     "#10b981",
        "REVIEW":    "#ec4899",
    }
    MILESTONES = ["요구 분석", "기능 개발", "검증", "PILOT", "REVIEW"]

    STATUS_COLORS = {
        "대기":   "#d97706",
        "진행중": "#2563eb",
        "완료":   "#059669",
        "취소":   "#dc2626",
        "미완료": "#d97706",
    }


# ============================================================
# Custom Widgets
# ============================================================
class RoundButton(tk.Canvas):
    """A modern-looking rounded button."""

    def __init__(self, parent, text="", command=None, bg_color=Theme.ACCENT_BLUE,
                 fg_color=Theme.WHITE, width=120, height=34, font_size=10, **kw):
        parent_bg = Theme.BG
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            pass
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                         highlightthickness=0, **kw)
        self._cmd = command
        self._bg_c = bg_color
        self._fg_c = fg_color
        self._text = text
        self._bw = width
        self._bh = height
        self._fs = font_size
        self._draw()
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._draw(self._lighten(self._bg_c)))
        self.bind("<Leave>", lambda e: self._draw())

    def _draw(self, color=None):
        self.delete("all")
        c = color or self._bg_c
        r, w, h = 8, self._bw, self._bh
        self.create_arc(0, 0, r * 2, r * 2, start=90, extent=90, fill=c, outline=c)
        self.create_arc(w - r * 2, 0, w, r * 2, start=0, extent=90, fill=c, outline=c)
        self.create_arc(0, h - r * 2, r * 2, h, start=180, extent=90, fill=c, outline=c)
        self.create_arc(w - r * 2, h - r * 2, w, h, start=270, extent=90, fill=c, outline=c)
        self.create_rectangle(r, 0, w - r, h, fill=c, outline=c)
        self.create_rectangle(0, r, w, h - r, fill=c, outline=c)
        self.create_text(w // 2, h // 2, text=self._text, fill=self._fg_c,
                         font=("맑은 고딕", self._fs, "bold"))

    def _click(self, e):
        if self._cmd:
            self._cmd()

    @staticmethod
    def _lighten(hex_color, factor=0.15):
        h = hex_color.lstrip("#")
        r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16)
        return f"#{min(255,int(r+(255-r)*factor)):02x}{min(255,int(g+(255-g)*factor)):02x}{min(255,int(b+(255-b)*factor)):02x}"


class StatusLabel(tk.Label):
    """Colored status label."""

    def __init__(self, parent, status="대기", **kw):
        color = Theme.STATUS_COLORS.get(status, Theme.TEXT_DIM)
        bg = parent.cget("bg") if hasattr(parent, "cget") else Theme.BG_CARD
        super().__init__(parent, text=f"  {status}  ", font=("맑은 고딕", 9, "bold"),
                         bg=bg, fg=color, **kw)


class ProgressCanvas(tk.Canvas):
    """Simple progress bar canvas."""

    def __init__(self, parent, value=0, bar_width=120, bar_height=8, **kw):
        parent_bg = Theme.BG_CARD
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            pass
        super().__init__(parent, width=bar_width, height=bar_height, bg=parent_bg,
                         highlightthickness=0, **kw)
        color = Theme.ACCENT_GREEN if value >= 80 else Theme.ACCENT_BLUE if value >= 40 else Theme.ACCENT_RED
        self.create_rectangle(0, 0, bar_width, bar_height, fill=Theme.BG_DARK, outline="")
        fw = int(bar_width * min(value, 100) / 100)
        if fw > 0:
            self.create_rectangle(0, 0, fw, bar_height, fill=color, outline="")


# ============================================================
# Main Application
# ============================================================
class MBOApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"MBO Project Leader v{__version__}")
        self.geometry("1200x750")
        self.minsize(950, 600)
        self.configure(bg=Theme.BG)
        self.attributes('-alpha', 1.0)    # fully opaque

        # Window icon (supports both script and PyInstaller --onefile)
        _base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        _icon_path = os.path.join(_base, "app_icon.ico")
        if os.path.exists(_icon_path):
            self.iconbitmap(_icon_path)

        # Application state
        self.current_year = datetime.now().year
        self.selected_project_id = None
        self.selected_date = date.today()
        self.current_page = "dashboard"
        self.project_sort = "priority_desc"   # default sort
        self.tracking_sort = "priority_desc"    # tracking sort

        self._setup_styles()
        self._build_layout()
        self._navigate("dashboard")

    def _setup_styles(self):
        """Configure ttk styles for dark theme."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=Theme.BG_INPUT, background=Theme.BG_INPUT,
                        foreground=Theme.TEXT, selectbackground=Theme.ACCENT_BLUE,
                        bordercolor=Theme.BORDER, arrowcolor=Theme.TEXT_DIM)
        style.map("TCombobox",
                  fieldbackground=[("readonly", Theme.BG_INPUT)],
                  selectbackground=[("readonly", Theme.BG_INPUT)],
                  selectforeground=[("readonly", Theme.TEXT)])

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------
    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=Theme.BG_DARK, width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Logo
        logo_f = tk.Frame(self.sidebar, bg=Theme.BG_DARK)
        logo_f.pack(fill=tk.X, padx=16, pady=(20, 24))
        tk.Label(logo_f, text="📊", font=("Segoe UI Emoji", 18),
                 bg=Theme.BG_DARK, fg=Theme.ACCENT_BLUE).pack(side=tk.LEFT)
        tk.Label(logo_f, text=" MBO Leader", font=("맑은 고딕", 14, "bold"),
                 bg=Theme.BG_DARK, fg=Theme.ACCENT_CYAN).pack(side=tk.LEFT, padx=(4, 0))

        # Navigation items
        self.nav_btns = {}
        nav_items = [
            ("관리", None), ("dashboard", "📋  대시보드"), ("projects", "📂  프로젝트"),
            ("monthly", "📅  월별 계획"), ("daily", "✅  일별 체크"),
            ("분석", None), ("tracking", "📈  추적/분석"), ("gantt", "📊  간트차트"),
            ("설정", None), ("years", "📆  연도 관리"),
        ]
        for key, label in nav_items:
            if label is None:
                tk.Label(self.sidebar, text=key, font=("맑은 고딕", 8, "bold"),
                         bg=Theme.BG_DARK, fg=Theme.TEXT_DARK, anchor="w").pack(
                    fill=tk.X, padx=20, pady=(16, 4))
            else:
                btn = tk.Label(self.sidebar, text=label, font=("맑은 고딕", 10),
                               bg=Theme.BG_DARK, fg=Theme.TEXT_DIM, anchor="w",
                               cursor="hand2", padx=20, pady=8)
                btn.pack(fill=tk.X, padx=8, pady=1)
                btn.bind("<Button-1>", lambda e, k=key: self._navigate(k))
                btn.bind("<Enter>", lambda e, b=btn, k=key: b.configure(bg=Theme.BG_CARD)
                         if k != self.current_page else None)
                btn.bind("<Leave>", lambda e, b=btn, k=key: b.configure(bg=Theme.BG_DARK)
                         if k != self.current_page else None)
                self.nav_btns[key] = btn

        # Bottom area: Notice button
        bottom_f = tk.Frame(self.sidebar, bg=Theme.BG_DARK)
        bottom_f.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 16))
        notice_btn = tk.Label(bottom_f, text="📢 공지사항", font=("맑은 고딕", 10),
                              bg=Theme.BG_CARD_HOVER, fg=Theme.TEXT, anchor="center",
                              cursor="hand2", padx=10, pady=6)
        notice_btn.pack(fill=tk.X)
        notice_btn.bind("<Button-1>", lambda e: self._show_notice())
        notice_btn.bind("<Enter>", lambda e: notice_btn.configure(bg=Theme.BG_CARD))
        notice_btn.bind("<Leave>", lambda e: notice_btn.configure(bg=Theme.BG_CARD_HOVER))

        # Main area
        self.main_area = tk.Frame(self, bg=Theme.BG)
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _show_notice(self):
        """app_history.md 파일을 읽어 공지사항 다이얼로그에 표시"""
        # app_history.md 경로: 스크립트(또는 EXE) 옆
        _base = getattr(sys, '_MEIPASS', None)
        paths_to_try = []
        if _base:
            paths_to_try.append(os.path.join(_base, "app_history.md"))
        paths_to_try.append(os.path.join(BASE_DIR, "app_history.md"))
        paths_to_try.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_history.md"))

        content = ""
        for p in paths_to_try:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    pass
                break
        if not content.strip():
            content = "등록된 공지사항이 없습니다."

        win = tk.Toplevel(self)
        win.title("📢 공지사항")
        win.geometry("560x480")
        win.configure(bg=Theme.BG_CARD)
        win.transient(self)
        win.grab_set()
        win.resizable(True, True)

        tk.Label(win, text="📢 공지사항 / 업데이트 히스토리",
                 font=("맑은 고딕", 14, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(pady=(20, 12), padx=24, anchor="w")

        txt_f = tk.Frame(win, bg=Theme.BG_CARD)
        txt_f.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 12))
        sb = tk.Scrollbar(txt_f)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt = tk.Text(txt_f, font=("맑은 고딕", 10), bg=Theme.BG_INPUT, fg=Theme.TEXT,
                      relief="flat", wrap="word", highlightthickness=1,
                      highlightbackground=Theme.BORDER, yscrollcommand=sb.set)
        txt.pack(fill=tk.BOTH, expand=True)
        sb.config(command=txt.yview)
        txt.insert("1.0", content)
        txt.configure(state="disabled")

        RoundButton(win, text="닫기", command=win.destroy,
                    bg_color=Theme.TEXT_DIM, width=80, height=32).pack(pady=(0, 16))

    def _navigate(self, page):
        self.current_page = page
        for k, b in self.nav_btns.items():
            if k == page:
                b.configure(bg=Theme.BG_CARD, fg=Theme.ACCENT_BLUE)
            else:
                b.configure(bg=Theme.BG_DARK, fg=Theme.TEXT_DIM)
        for w in self.main_area.winfo_children():
            w.destroy()
        {
            "dashboard": self._page_dashboard,
            "projects": self._page_projects,
            "monthly": self._page_monthly,
            "daily": self._page_daily,
            "tracking": self._page_tracking,
            "gantt": self._page_gantt,
            "years": self._page_years,
        }.get(page, self._page_dashboard)()

    # --------------------------------------------------------
    # Scrollable helper
    # --------------------------------------------------------
    def _scrollable(self, parent):
        canvas = tk.Canvas(parent, bg=Theme.BG, highlightthickness=0)
        sb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=Theme.BG)
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return frame

    # --------------------------------------------------------
    # Year selector combo
    # --------------------------------------------------------
    def _year_combo(self, parent, on_change=None):
        f = tk.Frame(parent, bg=parent.cget("bg"))
        conn = get_db()
        years = [r["year"] for r in conn.execute("SELECT year FROM years ORDER BY year DESC").fetchall()]
        conn.close()
        if not years:
            years = [datetime.now().year]
        if self.current_year not in years:
            self.current_year = years[0]

        tk.Label(f, text="연도:", font=("맑은 고딕", 10), bg=parent.cget("bg"),
                 fg=Theme.TEXT_DIM).pack(side=tk.LEFT, padx=(0, 6))
        var = tk.StringVar(value=str(self.current_year))
        cb = ttk.Combobox(f, textvariable=var, values=[str(y) for y in years],
                          width=8, state="readonly", font=("맑은 고딕", 10))
        cb.pack(side=tk.LEFT)

        def _changed(e):
            self.current_year = int(var.get())
            self.selected_project_id = None
            if on_change:
                on_change()
            else:
                self._navigate(self.current_page)

        cb.bind("<<ComboboxSelected>>", _changed)
        return f

    # --------------------------------------------------------
    # Project tabs
    # --------------------------------------------------------
    def _proj_tabs(self, parent, projects, refresh):
        tf = tk.Frame(parent, bg=Theme.BG)
        tf.pack(fill=tk.X, pady=(0, 16))
        for p in projects:
            act = p["id"] == self.selected_project_id
            bg = Theme.BG_CARD if act else Theme.BG
            fg = Theme.ACCENT_BLUE if act else Theme.TEXT_DIM
            lb = tk.Label(tf, text=p["name"],
                          font=("맑은 고딕", 10, "bold" if act else "normal"),
                          bg=bg, fg=fg, padx=16, pady=6, cursor="hand2")
            lb.pack(side=tk.LEFT, padx=(0, 4))
            lb.bind("<Button-1>", lambda e, pid=p["id"]:
                    (setattr(self, 'selected_project_id', pid), refresh()))

    # --------------------------------------------------------
    # Progress helper
    # --------------------------------------------------------
    @staticmethod
    def _calc_progress(conn, pid):
        t = conn.execute("SELECT COUNT(*) c FROM daily_tasks WHERE project_id=?", (pid,)).fetchone()["c"]
        d = conn.execute("SELECT COUNT(*) c FROM daily_tasks WHERE project_id=? AND is_done=1", (pid,)).fetchone()["c"]
        return round(d / t * 100) if t else 0

    # ============================================================
    # PAGE: Dashboard
    # ============================================================
    def _page_dashboard(self):
        frame = self._scrollable(self.main_area)
        ct = tk.Frame(frame, bg=Theme.BG)
        ct.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        # Header
        hd = tk.Frame(ct, bg=Theme.BG)
        hd.pack(fill=tk.X, pady=(0, 24))
        tk.Label(hd, text="📋 대시보드", font=("맑은 고딕", 20, "bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack(side=tk.LEFT)
        self._year_combo(hd).pack(side=tk.RIGHT)

        conn = get_db()
        projects = conn.execute("SELECT * FROM projects WHERE year=? ORDER BY priority DESC",
                                (self.current_year,)).fetchall()
        total_p = len(projects)
        done_p = sum(1 for p in projects if p["status"] == "완료")
        prog_p = sum(1 for p in projects if p["status"] == "진행중")
        progresses = [self._calc_progress(conn, p["id"]) for p in projects]
        avg_prog = round(sum(progresses) / len(progresses)) if progresses else 0

        today_str = date.today().isoformat()
        t_total = conn.execute(
            "SELECT COUNT(*) c FROM daily_tasks dt JOIN projects p ON dt.project_id=p.id WHERE p.year=? AND dt.task_date=?",
            (self.current_year, today_str)).fetchone()["c"]
        t_done = conn.execute(
            "SELECT COUNT(*) c FROM daily_tasks dt JOIN projects p ON dt.project_id=p.id WHERE p.year=? AND dt.task_date=? AND dt.is_done=1",
            (self.current_year, today_str)).fetchone()["c"]

        # Stats cards
        sf = tk.Frame(ct, bg=Theme.BG)
        sf.pack(fill=tk.X, pady=(0, 24))
        stats = [
            ("전체 프로젝트", str(total_p), Theme.ACCENT_BLUE),
            ("완료", str(done_p), Theme.ACCENT_GREEN),
            ("진행중", str(prog_p), Theme.ACCENT_CYAN),
            ("평균 달성률", f"{avg_prog}%", Theme.ACCENT_PURPLE),
            ("오늘 태스크", f"{t_done}/{t_total}", Theme.ACCENT_YELLOW),
        ]
        for i, (label, value, color) in enumerate(stats):
            c = tk.Frame(sf, bg=Theme.BG_CARD, padx=20, pady=16,
                         highlightbackground=Theme.BORDER, highlightthickness=1)
            c.grid(row=0, column=i, padx=(0, 12), sticky="nsew")
            sf.columnconfigure(i, weight=1)
            tk.Label(c, text=value, font=("맑은 고딕", 22, "bold"), bg=Theme.BG_CARD, fg=color).pack()
            tk.Label(c, text=label, font=("맑은 고딕", 9), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(pady=(4, 0))

        # Project table
        lc = tk.Frame(ct, bg=Theme.BG_CARD, padx=24, pady=20,
                       highlightbackground=Theme.BORDER, highlightthickness=1)
        lc.pack(fill=tk.BOTH, expand=True)
        tk.Label(lc, text="📂 프로젝트 현황", font=("맑은 고딕", 13, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(anchor="w", pady=(0, 16))

        if not projects:
            tk.Label(lc, text="📭 등록된 프로젝트가 없습니다.\n[프로젝트] 메뉴에서 추가하세요.",
                     font=("맑은 고딕", 11), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM, justify="center").pack(pady=40)
        else:
            # Header row
            hr = tk.Frame(lc, bg=Theme.BG_CARD)
            hr.pack(fill=tk.X, pady=(0, 6))
            for txt, w in [("프로젝트명", 18), ("가중치", 7), ("상태", 8), ("달성률", 18)]:
                tk.Label(hr, text=txt, font=("맑은 고딕", 9, "bold"),
                         bg=Theme.BG_CARD, fg=Theme.TEXT_DARK, width=w, anchor="center").pack(side=tk.LEFT, padx=2)

            for idx, p in enumerate(projects):
                prog = progresses[idx]
                rbg = Theme.BG_CARD_HOVER if idx % 2 == 0 else Theme.BG_CARD
                row = tk.Frame(lc, bg=rbg, padx=4, pady=8)
                row.pack(fill=tk.X)

                tk.Label(row, text=p["name"], font=("맑은 고딕", 10, "bold"),
                         bg=rbg, fg=Theme.TEXT, width=18, anchor="center").pack(side=tk.LEFT, padx=2)
                tk.Label(row, text=f"{p['weight']}%", font=("맑은 고딕", 9),
                         bg=rbg, fg=Theme.TEXT_DIM, width=7, anchor="center").pack(side=tk.LEFT, padx=2)
                sl = StatusLabel(row, status=p["status"])
                sl.configure(bg=rbg, width=8, anchor="center")
                sl.pack(side=tk.LEFT, padx=2)
                pf = tk.Frame(row, bg=rbg)
                pf.pack(side=tk.LEFT, padx=6)
                ProgressCanvas(pf, value=prog, bar_width=100, bar_height=8).pack(side=tk.LEFT)
                tk.Label(pf, text=f" {prog}%", font=("맑은 고딕", 9, "bold"),
                         bg=rbg, fg=Theme.ACCENT_BLUE).pack(side=tk.LEFT, padx=(4, 0))
        conn.close()

    # ============================================================
    # PAGE: Projects
    # ============================================================
    def _page_projects(self):
        frame = self._scrollable(self.main_area)
        ct = tk.Frame(frame, bg=Theme.BG)
        ct.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        hd = tk.Frame(ct, bg=Theme.BG)
        hd.pack(fill=tk.X, pady=(0, 20))
        tk.Label(hd, text="📂 프로젝트 관리", font=("맑은 고딕", 20, "bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack(side=tk.LEFT)
        bf = tk.Frame(hd, bg=Theme.BG)
        bf.pack(side=tk.RIGHT)
        self._year_combo(bf).pack(side=tk.LEFT, padx=(0, 12))
        RoundButton(bf, text="+ 프로젝트 추가", command=lambda: self._project_dialog(),
                    bg_color=Theme.ACCENT_BLUE, width=130, height=32).pack(side=tk.LEFT)

        # Sort bar
        sort_bar = tk.Frame(ct, bg=Theme.BG_CARD, padx=16, pady=8,
                            highlightbackground=Theme.BORDER, highlightthickness=1)
        sort_bar.pack(fill=tk.X, pady=(0, 12))
        tk.Label(sort_bar, text="정렬:", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(side=tk.LEFT, padx=(0, 8))

        sort_options = [
            ("priority_desc", "우선순위 ↓"), ("priority_asc", "우선순위 ↑"),
            ("name_asc", "이름 ↑"),        ("name_desc", "이름 ↓"),
            ("weight_desc", "가중치 ↓"),   ("weight_asc", "가중치 ↑"),
            ("status", "상태별"),           ("difficulty", "난이도별"),
            ("created_desc", "최신순"),     ("created_asc", "오래된순"),
        ]
        for key, label in sort_options:
            is_active = self.project_sort == key
            bg = Theme.ACCENT_BLUE if is_active else Theme.BG_CARD
            fg = Theme.WHITE if is_active else Theme.TEXT_DIM
            sl = tk.Label(sort_bar, text=label, font=("맑은 고딕", 9, "bold" if is_active else "normal"),
                          bg=bg, fg=fg, padx=10, pady=3, cursor="hand2")
            sl.pack(side=tk.LEFT, padx=(0, 4))
            sl.bind("<Button-1>", lambda e, k=key: self._set_project_sort(k))
            if not is_active:
                sl.bind("<Enter>", lambda e, s=sl: s.configure(bg=Theme.BG_CARD_HOVER))
                sl.bind("<Leave>", lambda e, s=sl: s.configure(bg=Theme.BG_CARD))

        conn = get_db()
        # Sort query mapping
        sort_sql = {
            "priority_desc": "ORDER BY priority DESC, id",
            "priority_asc":  "ORDER BY priority ASC, id",
            "name_asc":      "ORDER BY name COLLATE NOCASE ASC",
            "name_desc":     "ORDER BY name COLLATE NOCASE DESC",
            "weight_desc":   "ORDER BY weight DESC, id",
            "weight_asc":    "ORDER BY weight ASC, id",
            "status":        "ORDER BY CASE status WHEN '진행중' THEN 1 WHEN '대기' THEN 2 WHEN '완료' THEN 3 WHEN '취소' THEN 4 END, id",
            "difficulty":    "ORDER BY CASE difficulty WHEN '매우 어려움' THEN 1 WHEN '어려움' THEN 2 WHEN '보통' THEN 3 WHEN '쉬움' THEN 4 END, id",
            "created_desc":  "ORDER BY created_at DESC",
            "created_asc":   "ORDER BY created_at ASC",
        }.get(self.project_sort, "ORDER BY priority DESC, id")
        projects = conn.execute(f"SELECT * FROM projects WHERE year=? {sort_sql}",
                                (self.current_year,)).fetchall()

        if not projects:
            tk.Label(ct, text="📭 등록된 프로젝트가 없습니다.\n위 [+ 프로젝트 추가] 버튼으로 추가하세요.",
                     font=("맑은 고딕", 11), bg=Theme.BG, fg=Theme.TEXT_DIM, justify="center").pack(pady=60)
        else:
            for p in projects:
                prog = self._calc_progress(conn, p["id"])
                card = tk.Frame(ct, bg=Theme.BG_CARD, padx=20, pady=16,
                                highlightbackground=Theme.BORDER, highlightthickness=1)
                card.pack(fill=tk.X, pady=(0, 10))

                top = tk.Frame(card, bg=Theme.BG_CARD)
                top.pack(fill=tk.X)
                tk.Label(top, text=p["name"], font=("맑은 고딕", 13, "bold"),
                         bg=Theme.BG_CARD, fg=Theme.TEXT).pack(side=tk.LEFT)

                # Actions
                af = tk.Frame(top, bg=Theme.BG_CARD)
                af.pack(side=tk.RIGHT)
                eb = tk.Label(af, text="✏️ 수정", font=("맑은 고딕", 9), bg=Theme.BG_CARD,
                              fg=Theme.ACCENT_BLUE, cursor="hand2", padx=8)
                eb.pack(side=tk.LEFT)
                eb.bind("<Button-1>", lambda e, pid=p["id"]: self._project_dialog(pid))
                db = tk.Label(af, text="🗑️ 삭제", font=("맑은 고딕", 9), bg=Theme.BG_CARD,
                              fg=Theme.ACCENT_RED, cursor="hand2", padx=8)
                db.pack(side=tk.LEFT)
                db.bind("<Button-1>", lambda e, pid=p["id"]: self._delete_project(pid))

                StatusLabel(top, status=p["status"]).pack(side=tk.RIGHT, padx=8)

                # Info
                info = tk.Frame(card, bg=Theme.BG_CARD)
                info.pack(fill=tk.X, pady=(8, 0))
                diff = p["difficulty"] if "difficulty" in p.keys() else "보통"
                diff_colors = {"쉬움": Theme.ACCENT_GREEN, "보통": Theme.ACCENT_BLUE,
                               "어려움": Theme.ACCENT_YELLOW, "매우 어려움": Theme.ACCENT_RED}
                for lbl, val in [("가중치", f"{p['weight']}%"),
                                 ("우선순위", str(p["priority"])),
                                 ("난이도", diff)]:
                    tk.Label(info, text=f"{lbl}: ", font=("맑은 고딕", 9),
                             bg=Theme.BG_CARD, fg=Theme.TEXT_DARK).pack(side=tk.LEFT)
                    fg_c = diff_colors.get(val, Theme.TEXT_DIM) if lbl == "난이도" else Theme.TEXT_DIM
                    tk.Label(info, text=val, font=("맑은 고딕", 9, "bold"),
                             bg=Theme.BG_CARD, fg=fg_c).pack(side=tk.LEFT, padx=(0, 16))

                # Progress
                pf = tk.Frame(card, bg=Theme.BG_CARD)
                pf.pack(fill=tk.X, pady=(10, 0))
                ProgressCanvas(pf, value=prog, bar_width=300, bar_height=8).pack(side=tk.LEFT)
                tk.Label(pf, text=f" {prog}%", font=("맑은 고딕", 10, "bold"),
                         bg=Theme.BG_CARD, fg=Theme.ACCENT_BLUE).pack(side=tk.LEFT, padx=8)

                if p["description"]:
                    tk.Label(card, text=p["description"], font=("맑은 고딕", 9),
                             bg=Theme.BG_CARD, fg=Theme.TEXT_DIM, anchor="w",
                             wraplength=700, justify="left").pack(fill=tk.X, pady=(8, 0))
        conn.close()

    def _project_dialog(self, pid=None):
        data = {"name": "", "description": "", "kpi": "", "weight": 0, "priority": 1, "difficulty": "보통", "status": "대기"}
        if pid:
            conn = get_db()
            row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
            conn.close()
            if row:
                data = dict(row)

        win = tk.Toplevel(self)
        win.title("프로젝트 수정" if pid else "새 프로젝트 추가")
        win.geometry("480x540")
        win.configure(bg=Theme.BG_CARD)
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text="✏️ 프로젝트 수정" if pid else "➕ 새 프로젝트",
                 font=("맑은 고딕", 14, "bold"), bg=Theme.BG_CARD, fg=Theme.TEXT).pack(
            pady=(20, 16), padx=24, anchor="w")

        def _field(label_text, default="", is_text=False):
            tk.Label(win, text=label_text, font=("맑은 고딕", 9, "bold"),
                     bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w", padx=24, pady=(0, 4))
            if is_text:
                w = tk.Text(win, font=("맑은 고딕", 10), bg=Theme.BG_INPUT, fg=Theme.TEXT,
                            insertbackground=Theme.TEXT, relief="flat", height=3,
                            highlightthickness=1, highlightbackground=Theme.BORDER)
                w.pack(fill=tk.X, padx=24, pady=(0, 10))
                w.insert("1.0", default)
                return w
            else:
                v = tk.StringVar(value=default)
                tk.Entry(win, textvariable=v, font=("맑은 고딕", 10), bg=Theme.BG_INPUT,
                         fg=Theme.TEXT, insertbackground=Theme.TEXT, relief="flat",
                         highlightthickness=1, highlightbackground=Theme.BORDER).pack(
                    fill=tk.X, padx=24, pady=(0, 10), ipady=6)
                return v

        name_v = _field("프로젝트명 *", data["name"])
        desc_w = _field("설명", data["description"] or "", is_text=True)

        row1 = tk.Frame(win, bg=Theme.BG_CARD)
        row1.pack(fill=tk.X, padx=24, pady=(0, 10))
        # Weight
        f1 = tk.Frame(row1, bg=Theme.BG_CARD)
        f1.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        tk.Label(f1, text="가중치 (%)", font=("맑은 고딕", 9, "bold"), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(
            anchor="w")
        wt_v = tk.StringVar(value=str(data["weight"]))
        tk.Entry(f1, textvariable=wt_v, font=("맑은 고딕", 10), bg=Theme.BG_INPUT,
                 fg=Theme.TEXT, insertbackground=Theme.TEXT, relief="flat",
                 highlightthickness=1, highlightbackground=Theme.BORDER).pack(fill=tk.X, ipady=4)
        # Priority
        f2 = tk.Frame(row1, bg=Theme.BG_CARD)
        f2.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(8, 0))
        tk.Label(f2, text="우선순위", font=("맑은 고딕", 9, "bold"), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(
            anchor="w")
        pri_v = tk.StringVar(value=str(data["priority"]))
        ttk.Combobox(f2, textvariable=pri_v, values=["1", "2", "3", "4", "5"],
                     state="readonly", width=6, font=("맑은 고딕", 10)).pack(anchor="w")

        # Row2: Status + Difficulty
        row2 = tk.Frame(win, bg=Theme.BG_CARD)
        row2.pack(fill=tk.X, padx=24, pady=(0, 10))
        # Status
        f4 = tk.Frame(row2, bg=Theme.BG_CARD)
        f4.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        tk.Label(f4, text="상태", font=("맑은 고딕", 9, "bold"), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w")
        st_v = tk.StringVar(value=data["status"])
        ttk.Combobox(f4, textvariable=st_v, values=["대기", "진행중", "완료", "취소"],
                     state="readonly", width=8, font=("맑은 고딕", 10)).pack(anchor="w")
        # Difficulty
        f5 = tk.Frame(row2, bg=Theme.BG_CARD)
        f5.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(8, 0))
        tk.Label(f5, text="난이도", font=("맑은 고딕", 9, "bold"), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w")
        diff_v = tk.StringVar(value=data.get("difficulty", "보통"))
        ttk.Combobox(f5, textvariable=diff_v, values=["쉬움", "보통", "어려움", "매우 어려움"],
                     state="readonly", width=12, font=("맑은 고딕", 10)).pack(anchor="w")

        bframe = tk.Frame(win, bg=Theme.BG_CARD)
        bframe.pack(fill=tk.X, padx=24, pady=(20, 20))

        def save():
            nm = name_v.get().strip()
            if not nm:
                messagebox.showwarning("입력 오류", "프로젝트명을 입력하세요.", parent=win)
                return
            conn = get_db()
            try:
                w = float(wt_v.get())
            except ValueError:
                w = 0
            try:
                pr = int(pri_v.get())
            except ValueError:
                pr = 1
            df = diff_v.get()
            kpi_val = ""
            if pid:
                conn.execute("UPDATE projects SET name=?,description=?,kpi=?,weight=?,priority=?,difficulty=?,status=? WHERE id=?",
                             (nm, desc_w.get("1.0", "end").strip(), kpi_val, w, pr, df, st_v.get(), pid))
            else:
                conn.execute("INSERT OR IGNORE INTO years (year) VALUES (?)", (self.current_year,))
                conn.execute("INSERT INTO projects (year,name,description,kpi,weight,priority,difficulty,status) VALUES (?,?,?,?,?,?,?,?)",
                             (self.current_year, nm, desc_w.get("1.0", "end").strip(), kpi_val, w, pr, df, st_v.get()))
            conn.commit()
            conn.close()
            win.destroy()
            self._navigate("projects")

        RoundButton(bframe, text="취소", command=win.destroy, bg_color=Theme.TEXT_DIM, width=80, height=32).pack(
            side=tk.RIGHT, padx=(8, 0))
        RoundButton(bframe, text="저장", command=save, bg_color=Theme.ACCENT_BLUE, width=80, height=32).pack(
            side=tk.RIGHT)

    def _delete_project(self, pid):
        if messagebox.askyesno("삭제 확인", "정말 삭제하시겠습니까?\n관련 월별 계획과 일별 태스크도 삭제됩니다."):
            conn = get_db()
            conn.execute("DELETE FROM projects WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            self._navigate("projects")

    def _set_project_sort(self, key):
        self.project_sort = key
        self._navigate("projects")

    def _set_tracking_sort(self, key):
        self.tracking_sort = key
        self._navigate("tracking")

    # ============================================================
    # PAGE: Monthly Plans
    # ============================================================
    def _page_monthly(self):
        frame = self._scrollable(self.main_area)
        ct = tk.Frame(frame, bg=Theme.BG)
        ct.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        hd = tk.Frame(ct, bg=Theme.BG)
        hd.pack(fill=tk.X, pady=(0, 20))
        tk.Label(hd, text="📅 월별 계획", font=("맑은 고딕", 20, "bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack(side=tk.LEFT)
        self._year_combo(hd).pack(side=tk.RIGHT)

        conn = get_db()
        projects = conn.execute("SELECT * FROM projects WHERE year=? ORDER BY priority DESC",
                                (self.current_year,)).fetchall()

        if not projects:
            tk.Label(ct, text="📭 프로젝트가 없습니다. 먼저 프로젝트를 추가하세요.",
                     font=("맑은 고딕", 11), bg=Theme.BG, fg=Theme.TEXT_DIM).pack(pady=60)
            conn.close()
            return

        if not self.selected_project_id or not any(p["id"] == self.selected_project_id for p in projects):
            self.selected_project_id = projects[0]["id"]

        self._proj_tabs(ct, projects, lambda: self._navigate("monthly"))

        plans = conn.execute("SELECT * FROM monthly_plans WHERE project_id=? ORDER BY month",
                             (self.selected_project_id,)).fetchall()
        plan_map = {p["month"]: dict(p) for p in plans}
        conn.close()

        MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
        gf = tk.Frame(ct, bg=Theme.BG)
        gf.pack(fill=tk.BOTH, expand=True)

        for i, mn in enumerate(MONTHS):
            row, col = divmod(i, 4)
            plan = plan_map.get(i + 1, {})
            card = tk.Frame(gf, bg=Theme.BG_CARD, padx=16, pady=14,
                            highlightbackground=Theme.BORDER, highlightthickness=1, cursor="hand2")
            card.grid(row=row, column=col, padx=(0, 12), pady=(0, 12), sticky="nsew")
            gf.columnconfigure(col, weight=1)

            top = tk.Frame(card, bg=Theme.BG_CARD)
            top.pack(fill=tk.X)
            tk.Label(top, text=mn, font=("맑은 고딕", 12, "bold"), bg=Theme.BG_CARD, fg=Theme.TEXT).pack(side=tk.LEFT)
            status = plan.get("status", "미설정")
            StatusLabel(top, status=status).pack(side=tk.RIGHT)

            ms = plan.get("milestone", "")
            tgt = plan.get("target", "")
            if ms:
                ms_color = Theme.MILESTONE_COLORS.get(ms, Theme.TEXT_DIM)
                ms_f = tk.Frame(card, bg=Theme.BG_CARD)
                ms_f.pack(fill=tk.X, pady=(8, 0))
                ms_badge = tk.Label(ms_f, text=f" {ms} ", font=("맑은 고딕", 8, "bold"),
                                    bg=ms_color, fg=Theme.WHITE, padx=6, pady=1)
                ms_badge.pack(side=tk.LEFT)
                ms_badge.bind("<Button-1>", lambda e, m=i+1, pl=plan: self._monthly_dialog(m, pl))
            if tgt:
                tk.Label(card, text=f"목표: {tgt}", font=("맑은 고딕", 9),
                         bg=Theme.BG_CARD, fg=Theme.TEXT_DIM, anchor="w",
                         wraplength=200, justify="left").pack(fill=tk.X, pady=(2, 0))

            # Quick milestone buttons (always shown)
            qm_f = tk.Frame(card, bg=Theme.BG_CARD)
            qm_f.pack(fill=tk.X, pady=(6, 0))
            for ms_name in Theme.MILESTONES:
                ms_c = Theme.MILESTONE_COLORS[ms_name]
                is_set = ms == ms_name
                bg_c = ms_c if is_set else Theme.BG_CARD_HOVER
                fg_c = Theme.WHITE if is_set else Theme.TEXT_DARK
                qb = tk.Label(qm_f, text=ms_name[:2], font=("맑은 고딕", 7, "bold" if is_set else "normal"),
                              bg=bg_c, fg=fg_c, padx=3, pady=1, cursor="hand2")
                qb.pack(side=tk.LEFT, padx=(0, 2))
                qb.bind("<Button-1>", lambda e, m=i+1, mn2=ms_name: self._quick_set_milestone(m, mn2))
            # Clear milestone button (shown only when a milestone is set)
            if ms:
                clr = tk.Label(qm_f, text="✕", font=("맑은 고딕", 7, "bold"),
                               bg="#ef4444", fg=Theme.WHITE, padx=3, pady=1, cursor="hand2")
                clr.pack(side=tk.LEFT, padx=(4, 0))
                clr.bind("<Button-1>", lambda e, m=i+1: self._quick_set_milestone(m, None))

            # Quick milestone status buttons (미완료, 진행중, 완료)
            if ms:
                qs_f = tk.Frame(card, bg=Theme.BG_CARD)
                qs_f.pack(fill=tk.X, pady=(4, 0))
                tk.Label(qs_f, text="진행:", font=("맑은 고딕", 7), bg=Theme.BG_CARD,
                         fg=Theme.TEXT_DIM).pack(side=tk.LEFT, padx=(0, 4))
                ms_statuses = [("미완료", "#d97706"), ("진행중", "#2563eb"), ("완료", "#059669")]
                for s_name, s_color in ms_statuses:
                    is_cur = status == s_name
                    sb_bg = s_color if is_cur else Theme.BG_CARD_HOVER
                    sb_fg = Theme.WHITE if is_cur else Theme.TEXT_DARK
                    sb = tk.Label(qs_f, text=s_name, font=("맑은 고딕", 7, "bold" if is_cur else "normal"),
                                  bg=sb_bg, fg=sb_fg, padx=4, pady=1, cursor="hand2")
                    sb.pack(side=tk.LEFT, padx=(0, 2))
                    sb.bind("<Button-1>", lambda e, m=i+1, sn=s_name: self._quick_set_status(m, sn))

            if not ms and not tgt:
                tk.Label(card, text="클릭하여 상세 설정", font=("맑은 고딕", 8),
                         bg=Theme.BG_CARD, fg=Theme.TEXT_DARK, anchor="w").pack(fill=tk.X, pady=(4, 0))

            month_num = i + 1
            for widget in [card, top] + list(card.winfo_children()) + list(top.winfo_children()):
                widget.bind("<Button-1>", lambda e, m=month_num, pl=plan: self._monthly_dialog(m, pl))

    def _monthly_dialog(self, month, existing):
        MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
        win = tk.Toplevel(self)
        win.title(f"{MONTHS[month - 1]} 계획")
        win.geometry("440x440")
        win.configure(bg=Theme.BG_CARD)
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text=f"📅 {MONTHS[month - 1]} 계획", font=("맑은 고딕", 14, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(pady=(20, 16), padx=24, anchor="w")

        def _entry(label, default=""):
            tk.Label(win, text=label, font=("맑은 고딕", 9, "bold"),
                     bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w", padx=24, pady=(0, 4))
            v = tk.StringVar(value=default)
            tk.Entry(win, textvariable=v, font=("맑은 고딕", 10), bg=Theme.BG_INPUT,
                     fg=Theme.TEXT, insertbackground=Theme.TEXT, relief="flat",
                     highlightthickness=1, highlightbackground=Theme.BORDER).pack(
                fill=tk.X, padx=24, pady=(0, 10), ipady=6)
            return v

        # Milestone combobox with color indicator
        ms_v = tk.StringVar(value=existing.get("milestone", ""))
        tk.Label(win, text="마일스톤", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w", padx=24, pady=(0, 4))
        ms_frame = tk.Frame(win, bg=Theme.BG_CARD)
        ms_frame.pack(fill=tk.X, padx=24, pady=(0, 10))
        ms_cb = ttk.Combobox(ms_frame, textvariable=ms_v, values=Theme.MILESTONES,
                             state="readonly", font=("맑은 고딕", 10))
        ms_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ms_ind = tk.Label(ms_frame, text="  ● ", font=("맑은 고딕", 12),
                          bg=Theme.BG_CARD, fg=Theme.MILESTONE_COLORS.get(ms_v.get(), Theme.TEXT_DARK))
        ms_ind.pack(side=tk.LEFT, padx=(6, 0))
        def _ms_chg1(e=None):
            ms_ind.configure(fg=Theme.MILESTONE_COLORS.get(ms_v.get(), Theme.TEXT_DARK))
        ms_cb.bind("<<ComboboxSelected>>", _ms_chg1)

        tgt_v = _entry("목표", existing.get("target", ""))

        tk.Label(win, text="상태", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w", padx=24, pady=(0, 4))
        st_v = tk.StringVar(value=existing.get("status", "미완료"))
        ttk.Combobox(win, textvariable=st_v, values=["미완료", "진행중", "완료"],
                     state="readonly", font=("맑은 고딕", 10)).pack(anchor="w", padx=24, pady=(0, 10))

        tk.Label(win, text="비고", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w", padx=24, pady=(0, 4))
        note_w = tk.Text(win, font=("맑은 고딕", 10), bg=Theme.BG_INPUT, fg=Theme.TEXT,
                         insertbackground=Theme.TEXT, relief="flat", height=3,
                         highlightthickness=1, highlightbackground=Theme.BORDER)
        note_w.pack(fill=tk.X, padx=24, pady=(0, 10))
        note_w.insert("1.0", existing.get("note", ""))

        bf = tk.Frame(win, bg=Theme.BG_CARD)
        bf.pack(fill=tk.X, padx=24, pady=(10, 20))

        def save():
            conn = get_db()
            ex = conn.execute("SELECT id FROM monthly_plans WHERE project_id=? AND month=?",
                              (self.selected_project_id, month)).fetchone()
            if ex:
                conn.execute("UPDATE monthly_plans SET milestone=?,target=?,status=?,note=? WHERE project_id=? AND month=?",
                             (ms_v.get().strip(), tgt_v.get().strip(), st_v.get(),
                              note_w.get("1.0", "end").strip(), self.selected_project_id, month))
            else:
                conn.execute("INSERT INTO monthly_plans (project_id,month,milestone,target,status,note) VALUES (?,?,?,?,?,?)",
                             (self.selected_project_id, month, ms_v.get().strip(), tgt_v.get().strip(),
                              st_v.get(), note_w.get("1.0", "end").strip()))
            conn.commit()
            conn.close()
            win.destroy()
            self._navigate("monthly")

        RoundButton(bf, text="취소", command=win.destroy, bg_color=Theme.TEXT_DIM, width=80, height=32).pack(
            side=tk.RIGHT, padx=(8, 0))
        RoundButton(bf, text="저장", command=save, bg_color=Theme.ACCENT_BLUE, width=80, height=32).pack(side=tk.RIGHT)

    def _quick_set_status(self, month, status_name):
        """Quickly set milestone status (미완료/진행중/완료) for a month."""
        conn = get_db()
        ex = conn.execute("SELECT * FROM monthly_plans WHERE project_id=? AND month=?",
                          (self.selected_project_id, month)).fetchone()
        if ex:
            conn.execute("UPDATE monthly_plans SET status=? WHERE project_id=? AND month=?",
                         (status_name, self.selected_project_id, month))
        else:
            conn.execute("INSERT INTO monthly_plans (project_id,month,milestone,target,status,note) VALUES (?,?,?,?,?,?)",
                         (self.selected_project_id, month, "", "", status_name, ""))
        conn.commit()
        conn.close()
        self._navigate("monthly")

    def _quick_set_milestone(self, month, milestone_name):
        """Quickly set/toggle/clear a milestone for a month without opening dialog."""
        conn = get_db()
        ex = conn.execute("SELECT * FROM monthly_plans WHERE project_id=? AND month=?",
                          (self.selected_project_id, month)).fetchone()
        if ex:
            if milestone_name is None:
                new_ms = ""
            else:
                current_ms = ex["milestone"]
                new_ms = "" if current_ms == milestone_name else milestone_name
            conn.execute("UPDATE monthly_plans SET milestone=? WHERE project_id=? AND month=?",
                         (new_ms, self.selected_project_id, month))
        else:
            ms_val = "" if milestone_name is None else milestone_name
            conn.execute("INSERT INTO monthly_plans (project_id,month,milestone,target,status,note) VALUES (?,?,?,?,?,?)",
                         (self.selected_project_id, month, ms_val, "", "미완료", ""))
        conn.commit()
        conn.close()
        self._navigate("monthly")

    # ============================================================
    # PAGE: Daily Tasks
    # ============================================================
    def _page_daily(self):
        frame = self._scrollable(self.main_area)
        ct = tk.Frame(frame, bg=Theme.BG)
        ct.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        hd = tk.Frame(ct, bg=Theme.BG)
        hd.pack(fill=tk.X, pady=(0, 20))
        tk.Label(hd, text="✅ 일별 태스크", font=("맑은 고딕", 20, "bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack(side=tk.LEFT)
        bf = tk.Frame(hd, bg=Theme.BG)
        bf.pack(side=tk.RIGHT)
        self._year_combo(bf).pack(side=tk.LEFT, padx=(0, 12))
        RoundButton(bf, text="+ 태스크 추가", command=self._daily_dialog,
                    bg_color=Theme.ACCENT_GREEN, width=120, height=32).pack(side=tk.LEFT)

        conn = get_db()
        projects = conn.execute("SELECT * FROM projects WHERE year=? ORDER BY priority DESC",
                                (self.current_year,)).fetchall()

        if not projects:
            tk.Label(ct, text="📭 프로젝트가 없습니다.", font=("맑은 고딕", 11),
                     bg=Theme.BG, fg=Theme.TEXT_DIM).pack(pady=60)
            conn.close()
            return

        if not self.selected_project_id or not any(p["id"] == self.selected_project_id for p in projects):
            self.selected_project_id = projects[0]["id"]

        self._proj_tabs(ct, projects, lambda: self._navigate("daily"))

        body = tk.Frame(ct, bg=Theme.BG)
        body.pack(fill=tk.BOTH, expand=True)

        # Calendar
        sd = self.selected_date
        cal_c = tk.Frame(body, bg=Theme.BG_CARD, padx=16, pady=16,
                         highlightbackground=Theme.BORDER, highlightthickness=1)
        cal_c.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))

        ch = tk.Frame(cal_c, bg=Theme.BG_CARD)
        ch.pack(fill=tk.X, pady=(0, 12))
        prev_l = tk.Label(ch, text="◀", font=("맑은 고딕", 12), bg=Theme.BG_CARD,
                          fg=Theme.TEXT_DIM, cursor="hand2")
        prev_l.pack(side=tk.LEFT)
        prev_l.bind("<Button-1>", lambda e: self._change_cal_month(-1))
        tk.Label(ch, text=f"{sd.year}년 {sd.month}월", font=("맑은 고딕", 12, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(side=tk.LEFT, expand=True)
        next_l = tk.Label(ch, text="▶", font=("맑은 고딕", 12), bg=Theme.BG_CARD,
                          fg=Theme.TEXT_DIM, cursor="hand2")
        next_l.pack(side=tk.RIGHT)
        next_l.bind("<Button-1>", lambda e: self._change_cal_month(1))

        # Day of week headers
        cg = tk.Frame(cal_c, bg=Theme.BG_CARD)
        cg.pack(fill=tk.X)
        for i, dn in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
            fg = Theme.ACCENT_RED if i == 0 else Theme.ACCENT_BLUE if i == 6 else Theme.TEXT_DIM
            tk.Label(cg, text=dn, font=("맑은 고딕", 9, "bold"), bg=Theme.BG_CARD,
                     fg=fg, width=4).grid(row=0, column=i, pady=(0, 6))

        first_wd = (calendar.monthrange(sd.year, sd.month)[0] + 1) % 7
        days_in = calendar.monthrange(sd.year, sd.month)[1]
        today = date.today()

        # Get dates with tasks
        task_dates = set()
        rows = conn.execute(
            "SELECT DISTINCT task_date FROM daily_tasks WHERE project_id=? AND task_date LIKE ?",
            (self.selected_project_id, f"{sd.year}-{sd.month:02d}-%")).fetchall()
        for r in rows:
            task_dates.add(r["task_date"])

        r = 1
        c = first_wd
        for d in range(1, days_in + 1):
            dt = date(sd.year, sd.month, d)
            is_today = dt == today
            is_sel = dt == sd
            has_task = dt.isoformat() in task_dates

            bg = Theme.ACCENT_BLUE if is_sel else Theme.BG_CARD_HOVER if is_today else Theme.BG_CARD
            fg = Theme.WHITE if is_sel else Theme.ACCENT_CYAN if is_today else Theme.TEXT
            if c == 0 and not is_sel:
                fg = Theme.ACCENT_RED

            text = str(d)
            if has_task and not is_sel:
                text = f"·{d}"

            lbl = tk.Label(cg, text=text, font=("맑은 고딕", 9, "bold" if is_today or is_sel else "normal"),
                           bg=bg, fg=fg, width=4, height=1, cursor="hand2")
            lbl.grid(row=r, column=c, padx=1, pady=1)
            lbl.bind("<Button-1>", lambda e, d2=dt: self._sel_date(d2))

            c += 1
            if c > 6:
                c = 0
                r += 1

        # Task list
        tc = tk.Frame(body, bg=Theme.BG_CARD, padx=20, pady=16,
                      highlightbackground=Theme.BORDER, highlightthickness=1)
        tc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(tc, text=f"📝 {sd.isoformat()} 태스크",
                 font=("맑은 고딕", 13, "bold"), bg=Theme.BG_CARD, fg=Theme.TEXT).pack(anchor="w", pady=(0, 12))

        tasks = conn.execute("SELECT * FROM daily_tasks WHERE project_id=? AND task_date=? ORDER BY priority DESC, id",
                             (self.selected_project_id, sd.isoformat())).fetchall()

        if not tasks:
            tk.Label(tc, text="📝 이 날짜에 등록된 태스크가 없습니다.",
                     font=("맑은 고딕", 10), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(pady=40)
        else:
            for t in tasks:
                tf = tk.Frame(tc, bg=Theme.BG_CARD_HOVER, padx=12, pady=10)
                tf.pack(fill=tk.X, pady=(0, 6))

                var = tk.IntVar(value=t["is_done"])
                ckb = tk.Checkbutton(tf, variable=var, bg=Theme.BG_CARD_HOVER,
                                     activebackground=Theme.BG_CARD_HOVER, selectcolor=Theme.ACCENT_BLUE,
                                     command=lambda tid=t["id"], v=var: self._toggle_task(tid, v.get()))
                ckb.pack(side=tk.LEFT)

                tfg = Theme.TEXT_DIM if t["is_done"] else Theme.TEXT
                tfont = ("맑은 고딕", 10, "overstrike") if t["is_done"] else ("맑은 고딕", 10)
                tk.Label(tf, text=t["title"], font=tfont, bg=Theme.BG_CARD_HOVER,
                         fg=tfg, anchor="w").pack(side=tk.LEFT, padx=(4, 8), fill=tk.X, expand=True)

                if t["description"]:
                    tk.Label(tf, text=t["description"], font=("맑은 고딕", 8),
                             bg=Theme.BG_CARD_HOVER, fg=Theme.TEXT_DARK).pack(side=tk.LEFT, padx=(0, 8))

                tk.Label(tf, text="⭐" * min(t["priority"], 5), font=("맑은 고딕", 8),
                         bg=Theme.BG_CARD_HOVER, fg=Theme.TEXT_DIM).pack(side=tk.LEFT, padx=(0, 4))

                dl = tk.Label(tf, text="🗑️", font=("맑은 고딕", 10), bg=Theme.BG_CARD_HOVER,
                              fg=Theme.ACCENT_RED, cursor="hand2")
                dl.pack(side=tk.RIGHT)
                dl.bind("<Button-1>", lambda e, tid=t["id"]: self._del_task(tid))

        conn.close()

    def _sel_date(self, dt):
        self.selected_date = dt
        self._navigate("daily")

    def _change_cal_month(self, delta):
        sd = self.selected_date
        m = sd.month + delta
        y = sd.year
        if m > 12:
            m, y = 1, y + 1
        elif m < 1:
            m, y = 12, y - 1
        self.selected_date = date(y, m, 1)
        self._navigate("daily")

    def _toggle_task(self, tid, done):
        conn = get_db()
        conn.execute("UPDATE daily_tasks SET is_done=? WHERE id=?", (done, tid))
        conn.commit()
        conn.close()
        self._navigate("daily")

    def _del_task(self, tid):
        if messagebox.askyesno("삭제 확인", "태스크를 삭제하시겠습니까?"):
            conn = get_db()
            conn.execute("DELETE FROM daily_tasks WHERE id=?", (tid,))
            conn.commit()
            conn.close()
            self._navigate("daily")

    def _daily_dialog(self):
        if not self.selected_project_id:
            messagebox.showwarning("알림", "프로젝트를 먼저 선택하세요.")
            return

        win = tk.Toplevel(self)
        win.title("태스크 추가")
        win.geometry("420x370")
        win.configure(bg=Theme.BG_CARD)
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text="➕ 태스크 추가", font=("맑은 고딕", 14, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(pady=(20, 16), padx=24, anchor="w")

        def _entry(label, default=""):
            tk.Label(win, text=label, font=("맑은 고딕", 9, "bold"),
                     bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w", padx=24, pady=(0, 4))
            v = tk.StringVar(value=default)
            tk.Entry(win, textvariable=v, font=("맑은 고딕", 10), bg=Theme.BG_INPUT,
                     fg=Theme.TEXT, insertbackground=Theme.TEXT, relief="flat",
                     highlightthickness=1, highlightbackground=Theme.BORDER).pack(
                fill=tk.X, padx=24, pady=(0, 10), ipady=6)
            return v

        title_v = _entry("제목 *")
        desc_v = _entry("설명")

        row = tk.Frame(win, bg=Theme.BG_CARD)
        row.pack(fill=tk.X, padx=24, pady=(0, 10))
        f1 = tk.Frame(row, bg=Theme.BG_CARD)
        f1.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        tk.Label(f1, text="날짜 (YYYY-MM-DD)", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w")
        date_v = tk.StringVar(value=self.selected_date.isoformat())
        tk.Entry(f1, textvariable=date_v, font=("맑은 고딕", 10), bg=Theme.BG_INPUT,
                 fg=Theme.TEXT, insertbackground=Theme.TEXT, relief="flat",
                 highlightthickness=1, highlightbackground=Theme.BORDER).pack(fill=tk.X, ipady=4)

        f2 = tk.Frame(row, bg=Theme.BG_CARD)
        f2.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(8, 0))
        tk.Label(f2, text="우선순위", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w")
        pri_v = tk.StringVar(value="1")
        ttk.Combobox(f2, textvariable=pri_v, values=["1", "2", "3", "4", "5"],
                     state="readonly", width=6, font=("맑은 고딕", 10)).pack(anchor="w")

        bf = tk.Frame(win, bg=Theme.BG_CARD)
        bf.pack(fill=tk.X, padx=24, pady=(20, 20))

        def save():
            t = title_v.get().strip()
            if not t:
                messagebox.showwarning("입력 오류", "제목을 입력하세요.", parent=win)
                return
            td = date_v.get().strip()
            try:
                date.fromisoformat(td)
            except ValueError:
                messagebox.showwarning("입력 오류", "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)", parent=win)
                return
            try:
                pr = int(pri_v.get())
            except ValueError:
                pr = 1
            conn = get_db()
            conn.execute("INSERT INTO daily_tasks (project_id,task_date,title,description,priority) VALUES (?,?,?,?,?)",
                         (self.selected_project_id, td, t, desc_v.get().strip(), pr))
            conn.commit()
            conn.close()
            try:
                self.selected_date = date.fromisoformat(td)
            except ValueError:
                pass
            win.destroy()
            self._navigate("daily")

        RoundButton(bf, text="취소", command=win.destroy, bg_color=Theme.TEXT_DIM, width=80, height=32).pack(
            side=tk.RIGHT, padx=(8, 0))
        RoundButton(bf, text="추가", command=save, bg_color=Theme.ACCENT_GREEN, width=80, height=32).pack(
            side=tk.RIGHT)

    # ============================================================
    # PAGE: Tracking / Analytics
    # ============================================================
    def _page_tracking(self):
        frame = self._scrollable(self.main_area)
        ct = tk.Frame(frame, bg=Theme.BG)
        ct.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        hd = tk.Frame(ct, bg=Theme.BG)
        hd.pack(fill=tk.X, pady=(0, 20))
        tk.Label(hd, text="📈 추적 & 분석", font=("맑은 고딕", 20, "bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack(side=tk.LEFT)
        self._year_combo(hd).pack(side=tk.RIGHT)

        # Sort bar
        tsb = tk.Frame(ct, bg=Theme.BG_CARD, padx=16, pady=8,
                       highlightbackground=Theme.BORDER, highlightthickness=1)
        tsb.pack(fill=tk.X, pady=(0, 12))
        tk.Label(tsb, text="정렬:", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(side=tk.LEFT, padx=(0, 8))
        t_sort_opts = [
            ("priority_desc", "우선순위 ↓"), ("name_asc", "이름 ↑"),
            ("weight_desc", "가중치 ↓"), ("status", "상태별"),
            ("progress_desc", "달성률 ↓"), ("progress_asc", "달성률 ↑"),
        ]
        for key, label in t_sort_opts:
            is_active = self.tracking_sort == key
            bg = Theme.ACCENT_BLUE if is_active else Theme.BG_CARD
            fg = Theme.WHITE if is_active else Theme.TEXT_DIM
            tsl = tk.Label(tsb, text=label, font=("맑은 고딕", 9, "bold" if is_active else "normal"),
                           bg=bg, fg=fg, padx=10, pady=3, cursor="hand2")
            tsl.pack(side=tk.LEFT, padx=(0, 4))
            tsl.bind("<Button-1>", lambda e, k=key: self._set_tracking_sort(k))
            if not is_active:
                tsl.bind("<Enter>", lambda e, s=tsl: s.configure(bg=Theme.BG_CARD_HOVER))
                tsl.bind("<Leave>", lambda e, s=tsl: s.configure(bg=Theme.BG_CARD))

        conn = get_db()
        t_sort_sql = {
            "priority_desc": "ORDER BY priority DESC, id",
            "name_asc":      "ORDER BY name COLLATE NOCASE ASC",
            "weight_desc":   "ORDER BY weight DESC, id",
            "status":        "ORDER BY CASE status WHEN '진행중' THEN 1 WHEN '대기' THEN 2 WHEN '완료' THEN 3 WHEN '취소' THEN 4 END, id",
            "progress_desc": "ORDER BY priority DESC, id",
            "progress_asc":  "ORDER BY priority ASC, id",
        }.get(self.tracking_sort, "ORDER BY priority DESC, id")
        projects = conn.execute(f"SELECT * FROM projects WHERE year=? {t_sort_sql}",
                                (self.current_year,)).fetchall()

        if not projects:
            tk.Label(ct, text="📊 분석할 프로젝트가 없습니다.",
                     font=("맑은 고딕", 11), bg=Theme.BG, fg=Theme.TEXT_DIM).pack(pady=60)
            conn.close()
            return

        # Calculate progress for sorting
        proj_data = []
        for p in projects:
            prog = self._calc_progress(conn, p["id"])
            proj_data.append((p, prog))
        if self.tracking_sort == "progress_desc":
            proj_data.sort(key=lambda x: x[1], reverse=True)
        elif self.tracking_sort == "progress_asc":
            proj_data.sort(key=lambda x: x[1])

        for p, prog in proj_data:
            plans = conn.execute("SELECT * FROM monthly_plans WHERE project_id=? ORDER BY month",
                                 (p["id"],)).fetchall()
            comp_m = sum(1 for pl in plans if pl["status"] == "완료")
            total_m = max(sum(1 for pl in plans if pl["milestone"]), 1)
            mprog = round(comp_m / total_m * 100)

            total_t = conn.execute("SELECT COUNT(*) c FROM daily_tasks WHERE project_id=?", (p["id"],)).fetchone()["c"]
            done_t = conn.execute("SELECT COUNT(*) c FROM daily_tasks WHERE project_id=? AND is_done=1",
                                  (p["id"],)).fetchone()["c"]

            card = tk.Frame(ct, bg=Theme.BG_CARD, padx=24, pady=20,
                            highlightbackground=Theme.BORDER, highlightthickness=1)
            card.pack(fill=tk.X, pady=(0, 16))

            # Title
            tr = tk.Frame(card, bg=Theme.BG_CARD)
            tr.pack(fill=tk.X, pady=(0, 16))
            tk.Label(tr, text=p["name"], font=("맑은 고딕", 14, "bold"),
                     bg=Theme.BG_CARD, fg=Theme.TEXT).pack(side=tk.LEFT)
            StatusLabel(tr, status=p["status"]).pack(side=tk.RIGHT)

            # Stats
            sr = tk.Frame(card, bg=Theme.BG_CARD)
            sr.pack(fill=tk.X, pady=(0, 16))
            for label, value, color in [
                ("태스크 달성률", f"{prog}%", Theme.ACCENT_BLUE),
                ("월별 달성률", f"{mprog}%", Theme.ACCENT_CYAN),
                ("가중치", f"{p['weight']}%", Theme.ACCENT_PURPLE),
                ("완료 태스크", f"{done_t}/{total_t}", Theme.ACCENT_GREEN),
            ]:
                sf = tk.Frame(sr, bg=Theme.BG_CARD)
                sf.pack(side=tk.LEFT, expand=True)
                tk.Label(sf, text=value, font=("맑은 고딕", 18, "bold"), bg=Theme.BG_CARD, fg=color).pack()
                tk.Label(sf, text=label, font=("맑은 고딕", 8), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack()

            # Progress bar
            tk.Label(card, text="전체 진행률", font=("맑은 고딕", 9),
                     bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(anchor="w", pady=(0, 4))
            ProgressCanvas(card, value=prog, bar_width=500, bar_height=10).pack(anchor="w")

            # Monthly indicators
            mf = tk.Frame(card, bg=Theme.BG_CARD)
            mf.pack(anchor="w", pady=(12, 0))
            pm = {pl["month"]: dict(pl) for pl in plans}
            for m in range(1, 13):
                pl = pm.get(m, {})
                st = pl.get("status", "") if pl else ""
                bg = Theme.ACCENT_GREEN if st == "완료" else Theme.ACCENT_BLUE if st == "진행중" else Theme.BG_DARK
                fg = Theme.WHITE if st in ("완료", "진행중") else Theme.TEXT_DARK
                tk.Label(mf, text=str(m), font=("맑은 고딕", 8, "bold"), bg=bg, fg=fg,
                         width=3, height=1).pack(side=tk.LEFT, padx=1)

        conn.close()

    # ============================================================
    # PAGE: Gantt Chart
    # ============================================================
    def _page_gantt(self):
        frame = self._scrollable(self.main_area)
        ct = tk.Frame(frame, bg=Theme.BG)
        ct.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        # Header
        hd = tk.Frame(ct, bg=Theme.BG)
        hd.pack(fill=tk.X, pady=(0, 20))
        tk.Label(hd, text="📊 간트차트", font=("맑은 고딕", 20, "bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack(side=tk.LEFT)
        self._year_combo(hd).pack(side=tk.RIGHT)

        conn = get_db()
        projects = conn.execute(
            "SELECT * FROM projects WHERE year=? ORDER BY priority DESC, id",
            (self.current_year,)).fetchall()

        if not projects:
            tk.Label(ct, text="📭 프로젝트가 없습니다. 먼저 프로젝트를 추가하세요.",
                     font=("맑은 고딕", 11), bg=Theme.BG, fg=Theme.TEXT_DIM).pack(pady=60)
            conn.close()
            return

        # Legend (status colors only — 미설정 is hidden)
        legend_f = tk.Frame(ct, bg=Theme.BG)
        legend_f.pack(fill=tk.X, pady=(0, 12))
        for status, color in [("완료", Theme.ACCENT_GREEN), ("진행중", Theme.ACCENT_BLUE),
                               ("미완료", Theme.ACCENT_YELLOW)]:
            tk.Canvas(legend_f, width=14, height=14, bg=Theme.BG, highlightthickness=0).pack(side=tk.LEFT, padx=(0, 2))
            c_leg = legend_f.winfo_children()[-1]
            c_leg.create_rectangle(0, 0, 14, 14, fill=color, outline=color)
            tk.Label(legend_f, text=status, font=("맑은 고딕", 9),
                     bg=Theme.BG, fg=Theme.TEXT_DIM).pack(side=tk.LEFT, padx=(0, 14))
        tk.Label(legend_f, text="💡 막대/빈 셀을 클릭하면 해당 월 계획을 편집할 수 있습니다.",
                 font=("맑은 고딕", 8), bg=Theme.BG, fg=Theme.TEXT_DARK).pack(side=tk.RIGHT)

        # Gantt chart container
        chart_card = tk.Frame(ct, bg=Theme.BG_CARD, padx=2, pady=2,
                              highlightbackground=Theme.BORDER, highlightthickness=1)
        chart_card.pack(fill=tk.BOTH, expand=True)

        # Dimensions
        MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월",
                  "7월", "8월", "9월", "10월", "11월", "12월"]
        ROW_H = 48          # row height per project
        LABEL_W = 160       # left label column width
        MONTH_W = 62        # each month column width
        HEADER_H = 34       # column header height
        chart_w = LABEL_W + MONTH_W * 12 + 20
        chart_h = HEADER_H + ROW_H * len(projects) + 10

        gantt = tk.Canvas(chart_card, width=chart_w, height=chart_h,
                          bg=Theme.BG_CARD, highlightthickness=0)
        gantt.pack(padx=10, pady=10)

        # ── Draw month header ──
        for i, mn in enumerate(MONTHS):
            x0 = LABEL_W + i * MONTH_W
            x1 = x0 + MONTH_W
            gantt.create_rectangle(x0, 0, x1, HEADER_H,
                                   fill=Theme.BG_CARD_HOVER, outline=Theme.BORDER)
            gantt.create_text((x0 + x1) / 2, HEADER_H / 2, text=mn,
                              font=("맑은 고딕", 9, "bold"), fill=Theme.TEXT)

        # ── Draw current-month highlight stripe ──
        cur_month = datetime.now().month
        cx0 = LABEL_W + (cur_month - 1) * MONTH_W
        cx1 = cx0 + MONTH_W
        gantt.create_rectangle(cx0, HEADER_H, cx1, chart_h,
                               fill="#dbeafe", outline="")

        # ── Store bar→project mapping for click events ──
        self._gantt_bars = {}

        for idx, p in enumerate(projects):
            y0 = HEADER_H + idx * ROW_H
            y1 = y0 + ROW_H

            # Alternating row background
            row_bg = Theme.BG_CARD_HOVER if idx % 2 == 0 else Theme.BG_CARD
            gantt.create_rectangle(0, y0, LABEL_W, y1, fill=row_bg, outline=Theme.BORDER)

            # Project name label
            gantt.create_text(12, (y0 + y1) / 2, text=p["name"],
                              font=("맑은 고딕", 9, "bold"), fill=Theme.TEXT,
                              anchor="w", width=LABEL_W - 20)

            # Grid lines for months
            for i in range(12):
                x0 = LABEL_W + i * MONTH_W
                x1 = x0 + MONTH_W
                gantt.create_rectangle(x0, y0, x1, y1, fill="", outline=Theme.BORDER,
                                       dash=(2, 4))

            # Get monthly plans for this project
            plans = conn.execute(
                "SELECT * FROM monthly_plans WHERE project_id=? ORDER BY month",
                (p["id"],)).fetchall()
            plan_map = {pl["month"]: dict(pl) for pl in plans}

            # Determine contiguous bar spans by status
            bar_y0 = y0 + 10
            bar_y1 = y1 - 10

            for m in range(1, 13):
                plan = plan_map.get(m, {})
                status = plan.get("status", "")
                has_content = plan.get("milestone", "") or plan.get("target", "")

                if not status and not has_content:
                    continue  # truly empty — no bar

                # Skip 미설정 (no status set and no meaningful content)
                if not status or (status not in ("완료", "진행중", "미완료") and not has_content):
                    continue

                # Gantt bar color: based on status only
                if status == "완료":
                    bar_color = Theme.ACCENT_GREEN
                elif status == "진행중":
                    bar_color = Theme.ACCENT_BLUE
                elif status == "미완료":
                    bar_color = Theme.ACCENT_YELLOW
                else:
                    continue  # don't show 미설정

                bx0 = LABEL_W + (m - 1) * MONTH_W + 3
                bx1 = bx0 + MONTH_W - 6

                bar_id = gantt.create_rectangle(
                    bx0, bar_y0, bx1, bar_y1,
                    fill=bar_color, outline=bar_color, width=0,
                )
                gantt.create_rectangle(
                    bx0, bar_y0, bx1, bar_y1,
                    fill="", outline=Theme.WHITE, width=1,
                )

                # Milestone text on bar (gray color)
                bar_text = plan.get("milestone", "") or plan.get("target", "")
                if bar_text:
                    gantt.create_text(
                        (bx0 + bx1) / 2, (bar_y0 + bar_y1) / 2,
                        text=bar_text[:6],
                        font=("맑은 고딕", 7), fill="#6b7280",
                        width=MONTH_W - 12,
                    )

                # Store mapping for click
                self._gantt_bars[bar_id] = {
                    "project_id": p["id"],
                    "month": m,
                    "plan": plan,
                }

        conn.close()

        # ── Click handler ──
        def _on_bar_click(event):
            item = gantt.find_closest(event.x, event.y)
            if item and item[0] in self._gantt_bars:
                info = self._gantt_bars[item[0]]
                self.selected_project_id = info["project_id"]
                self._gantt_monthly_dialog(info["month"], info["plan"])

        gantt.bind("<Button-1>", _on_bar_click)

        # ── Empty-cell click handler (to create new plan) ──
        def _on_empty_click(event):
            # Check if click is in chart area (not on an existing bar)
            items = gantt.find_overlapping(event.x - 2, event.y - 2,
                                           event.x + 2, event.y + 2)
            for it in items:
                if it in self._gantt_bars:
                    return  # already handled by bar click

            if event.x < LABEL_W or event.y < HEADER_H:
                return
            col = (event.x - LABEL_W) // MONTH_W
            row = (event.y - HEADER_H) // ROW_H
            if 0 <= col < 12 and 0 <= row < len(projects):
                month = int(col) + 1
                pid = projects[int(row)]["id"]
                self.selected_project_id = pid
                plan = {}
                c2 = get_db()
                ex = c2.execute(
                    "SELECT * FROM monthly_plans WHERE project_id=? AND month=?",
                    (pid, month)).fetchone()
                if ex:
                    plan = dict(ex)
                c2.close()
                self._gantt_monthly_dialog(month, plan)

        gantt.bind("<Button-1>", _on_empty_click, add="+")

    def _gantt_monthly_dialog(self, month, existing):
        """Open monthly plan dialog and refresh Gantt chart after save."""
        MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월",
                  "7월", "8월", "9월", "10월", "11월", "12월"]
        win = tk.Toplevel(self)
        win.title(f"{MONTHS[month - 1]} 계획 (간트차트)")
        win.geometry("440x440")
        win.configure(bg=Theme.BG_CARD)
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text=f"📅 {MONTHS[month - 1]} 계획",
                 font=("맑은 고딕", 14, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(
            pady=(20, 16), padx=24, anchor="w")

        def _entry(label, default=""):
            tk.Label(win, text=label, font=("맑은 고딕", 9, "bold"),
                     bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(
                anchor="w", padx=24, pady=(0, 4))
            v = tk.StringVar(value=default)
            tk.Entry(win, textvariable=v, font=("맑은 고딕", 10),
                     bg=Theme.BG_INPUT, fg=Theme.TEXT,
                     insertbackground=Theme.TEXT, relief="flat",
                     highlightthickness=1, highlightbackground=Theme.BORDER).pack(
                fill=tk.X, padx=24, pady=(0, 10), ipady=6)
            return v

        # Milestone combobox with color indicator
        ms_v = tk.StringVar(value=existing.get("milestone", ""))
        tk.Label(win, text="마일스톤", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(
            anchor="w", padx=24, pady=(0, 4))
        ms_frame2 = tk.Frame(win, bg=Theme.BG_CARD)
        ms_frame2.pack(fill=tk.X, padx=24, pady=(0, 10))
        ms_cb2 = ttk.Combobox(ms_frame2, textvariable=ms_v, values=Theme.MILESTONES,
                              state="readonly", font=("맑은 고딕", 10))
        ms_cb2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ms_ind2 = tk.Label(ms_frame2, text="  ● ", font=("맑은 고딕", 12),
                           bg=Theme.BG_CARD, fg=Theme.MILESTONE_COLORS.get(ms_v.get(), Theme.TEXT_DARK))
        ms_ind2.pack(side=tk.LEFT, padx=(6, 0))
        def _ms_chg2(e=None):
            ms_ind2.configure(fg=Theme.MILESTONE_COLORS.get(ms_v.get(), Theme.TEXT_DARK))
        ms_cb2.bind("<<ComboboxSelected>>", _ms_chg2)

        tgt_v = _entry("목표", existing.get("target", ""))

        tk.Label(win, text="상태", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(
            anchor="w", padx=24, pady=(0, 4))
        st_v = tk.StringVar(value=existing.get("status", "미완료"))
        ttk.Combobox(win, textvariable=st_v,
                     values=["미완료", "진행중", "완료"],
                     state="readonly", font=("맑은 고딕", 10)).pack(
            anchor="w", padx=24, pady=(0, 10))

        tk.Label(win, text="비고", font=("맑은 고딕", 9, "bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM).pack(
            anchor="w", padx=24, pady=(0, 4))
        note_w = tk.Text(win, font=("맑은 고딕", 10), bg=Theme.BG_INPUT,
                         fg=Theme.TEXT, insertbackground=Theme.TEXT,
                         relief="flat", height=3,
                         highlightthickness=1, highlightbackground=Theme.BORDER)
        note_w.pack(fill=tk.X, padx=24, pady=(0, 10))
        note_w.insert("1.0", existing.get("note", ""))

        bf = tk.Frame(win, bg=Theme.BG_CARD)
        bf.pack(fill=tk.X, padx=24, pady=(10, 20))

        def save():
            conn = get_db()
            ex = conn.execute(
                "SELECT id FROM monthly_plans WHERE project_id=? AND month=?",
                (self.selected_project_id, month)).fetchone()
            if ex:
                conn.execute(
                    "UPDATE monthly_plans SET milestone=?,target=?,status=?,note=? "
                    "WHERE project_id=? AND month=?",
                    (ms_v.get().strip(), tgt_v.get().strip(), st_v.get(),
                     note_w.get("1.0", "end").strip(),
                     self.selected_project_id, month))
            else:
                conn.execute(
                    "INSERT INTO monthly_plans "
                    "(project_id,month,milestone,target,status,note) "
                    "VALUES (?,?,?,?,?,?)",
                    (self.selected_project_id, month,
                     ms_v.get().strip(), tgt_v.get().strip(),
                     st_v.get(), note_w.get("1.0", "end").strip()))
            conn.commit()
            conn.close()
            win.destroy()
            self._navigate("gantt")

        RoundButton(bf, text="취소", command=win.destroy,
                    bg_color=Theme.TEXT_DIM, width=80, height=32).pack(
            side=tk.RIGHT, padx=(8, 0))
        RoundButton(bf, text="저장", command=save,
                    bg_color=Theme.ACCENT_BLUE, width=80, height=32).pack(
            side=tk.RIGHT)

    # ============================================================
    # PAGE: Year Management
    # ============================================================
    def _page_years(self):
        frame = self._scrollable(self.main_area)
        ct = tk.Frame(frame, bg=Theme.BG)
        ct.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        hd = tk.Frame(ct, bg=Theme.BG)
        hd.pack(fill=tk.X, pady=(0, 24))
        tk.Label(hd, text="📆 연도 관리", font=("맑은 고딕", 20, "bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack(side=tk.LEFT)
        RoundButton(hd, text="+ 연도 추가", command=self._add_year,
                    bg_color=Theme.ACCENT_BLUE, width=120, height=32).pack(side=tk.RIGHT)

        conn = get_db()
        years = [r["year"] for r in conn.execute("SELECT year FROM years ORDER BY year DESC").fetchall()]

        card = tk.Frame(ct, bg=Theme.BG_CARD, padx=24, pady=24,
                        highlightbackground=Theme.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        if not years:
            tk.Label(card, text="📆 관리 중인 연도가 없습니다.\n[+ 연도 추가]를 눌러 추가하세요.",
                     font=("맑은 고딕", 11), bg=Theme.BG_CARD, fg=Theme.TEXT_DIM, justify="center").pack(pady=60)
        else:
            gf = tk.Frame(card, bg=Theme.BG_CARD)
            gf.pack()
            for i, y in enumerate(years):
                pc = conn.execute("SELECT COUNT(*) c FROM projects WHERE year=?", (y,)).fetchone()["c"]
                yc = tk.Frame(gf, bg=Theme.BG_CARD_HOVER, padx=28, pady=20, cursor="hand2",
                              highlightbackground=Theme.BORDER, highlightthickness=1)
                yc.grid(row=i // 5, column=i % 5, padx=8, pady=8)

                tk.Label(yc, text=str(y), font=("맑은 고딕", 20, "bold"),
                         bg=Theme.BG_CARD_HOVER, fg=Theme.ACCENT_BLUE, cursor="hand2").pack()
                tk.Label(yc, text=f"프로젝트 {pc}개", font=("맑은 고딕", 9),
                         bg=Theme.BG_CARD_HOVER, fg=Theme.TEXT_DIM, cursor="hand2").pack(pady=(4, 0))

                for w in [yc] + list(yc.winfo_children()):
                    w.bind("<Button-1>", lambda e, yr=y: self._goto_year(yr))

        conn.close()

    def _add_year(self):
        y_str = simpledialog.askstring("연도 추가", "추가할 연도를 입력하세요:",
                                       initialvalue=str(datetime.now().year), parent=self)
        if not y_str:
            return
        try:
            y = int(y_str)
            if y < 2000 or y > 2100:
                raise ValueError
        except ValueError:
            messagebox.showwarning("입력 오류", "올바른 연도를 입력하세요. (2000~2100)")
            return
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO years (year) VALUES (?)", (y,))
        conn.commit()
        conn.close()
        self.current_year = y
        self._navigate("years")

    def _goto_year(self, year):
        self.current_year = year
        self._navigate("dashboard")


# ============================================================
# Entry Point
# ============================================================
def main():
    init_db()
    app = MBOApp()
    # 실행 후 백그라운드에서 업데이트 확인 (UI 블로킹 없음)
    check_update_async(app)
    app.mainloop()


if __name__ == "__main__":
    main()
