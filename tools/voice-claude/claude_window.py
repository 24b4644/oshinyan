"""Claude デスクトップアプリ（Windows）の操作：前面に出す・入力して送信・返答を読み取る。"""
import os
import subprocess
import time

import pyperclip
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

import config
from text_utils import extract_answer, normalize


class ClaudeWindow:
    def __init__(self):
        self.desktop = Desktop(backend="uia")

    # ---- ウィンドウ ---------------------------------------------------------
    def _spec(self):
        return self.desktop.window(title_re=config.CLAUDE_WINDOW_TITLE_RE,
                                   found_index=0)

    def get(self, launch=True, timeout=20):
        spec = self._spec()
        if spec.exists(timeout=1):
            return spec.wrapper_object()
        if not launch:
            return None
        if not os.path.exists(config.CLAUDE_EXE):
            raise RuntimeError(
                f"Claude アプリが見つかりません: {config.CLAUDE_EXE}\n"
                "config.py の CLAUDE_EXE を確認してください。")
        subprocess.Popen([config.CLAUDE_EXE, *config.CLAUDE_ARGS])
        if not spec.exists(timeout=timeout):
            raise RuntimeError("Claude アプリのウィンドウが開きませんでした。")
        time.sleep(2)
        return spec.wrapper_object()

    def bring_to_front(self):
        win = self.get()
        try:
            if win.is_minimized():
                win.restore()
        except Exception:
            pass
        win.set_focus()
        time.sleep(0.4)
        return win

    # ---- 入力 --------------------------------------------------------------
    def _focus_input(self, win):
        """入力欄をクリックする。見つからなければ何もしない（通常は既にフォーカス済み）。"""
        try:
            edits = win.descendants(control_type="Edit")
            if edits:
                edits[-1].click_input()
                time.sleep(0.2)
                return True
        except Exception:
            pass
        return False

    def send(self, text):
        win = self.bring_to_front()
        self._focus_input(win)
        try:
            old_clip = pyperclip.paste()
        except Exception:
            old_clip = None
        pyperclip.copy(text)
        send_keys("^v")
        time.sleep(0.3)
        send_keys("{ENTER}")
        time.sleep(0.3)
        if old_clip is not None:
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass

    # ---- 読み取り -----------------------------------------------------------
    def read_screen_text(self):
        win = self.get(launch=False)
        if win is None:
            return ""
        parts = []
        for el in win.descendants(control_type="Text"):
            try:
                t = el.window_text()
            except Exception:
                continue
            if t and t.strip():
                parts.append(t.strip())
        return "\n".join(parts)

    def wait_answer(self, question, on_progress=None):
        """返答の文字が一定時間変わらなくなるまで待って返す。"""
        start = time.time()
        last, last_change = "", time.time()
        while time.time() - start < config.ANSWER_TIMEOUT_SEC:
            time.sleep(1.0)
            try:
                screen = self.read_screen_text()
            except Exception:
                continue
            ans = extract_answer(screen, question, config.UI_NOISE_LINES)
            if normalize(ans) != normalize(last):
                last, last_change = ans, time.time()
                if on_progress:
                    on_progress(len(ans))
            elif ans and time.time() - last_change >= config.ANSWER_STABLE_SEC:
                return ans
        return last
