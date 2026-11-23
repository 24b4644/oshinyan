"""設定ファイル。必要に応じて値を書き換えてください。"""
import os

# ---- ウェイクワード -------------------------------------------------------
# 音声認識結果をカタカナに正規化したあと、以下のどれかを含めば起動します。
# 反応しにくい場合は、コンソールに表示される「[聞こえた]」の文字を見て追加してください。
WAKE_PATTERNS = [
    "ネエクロード",
    "ネークロード",
    "ネクロード",
    "ネエクロウド",
    "ネエクロド",
    "ネエクラウド",
]
# True にすると「クロード」だけでも起動します（反応しやすいが誤作動も増えます）
WAKE_LOOSE = False
LOOSE_PATTERNS = ["クロード", "クロウド"]

# ---- 音声認識 -------------------------------------------------------------
# ウェイクワード検知用の Vosk 日本語モデルのフォルダ（setup.bat が自動で置きます）
VOSK_MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
# 質問の聞き取りエンジン: "google"（高精度・要ネット） / "vosk"（オフライン・精度低め）
QUESTION_STT = "google"
SAMPLE_RATE = 16000
# 話し始めを待つ最大秒数 / 話し終わりと判断する無音秒数 / 質問の最大秒数
WAIT_FOR_SPEECH_SEC = 6.0
END_SILENCE_SEC = 1.2
MAX_QUESTION_SEC = 20.0
# マイク音量のしきい値（None なら起動時に周囲の雑音から自動で決めます）
SPEECH_RMS_THRESHOLD = None

# ---- Claude アプリ --------------------------------------------------------
# Claude デスクトップアプリのウィンドウタイトル（正規表現）
# ブラウザ版を使う場合の例: r".*Claude.*(Microsoft Edge|Google Chrome).*"
CLAUDE_WINDOW_TITLE_RE = r"^Claude$"
# アプリが起動していないときに起動する実行ファイル
CLAUDE_EXE = os.path.expandvars(r"%LOCALAPPDATA%\AnthropicClaude\claude.exe")
# 画面の文字を読み取れるように、アクセシビリティを有効にして起動します
CLAUDE_ARGS = ["--force-renderer-accessibility"]
# 返答の文字が何秒変化しなければ「書き終わった」と判断するか
ANSWER_STABLE_SEC = 3.0
# 返答を待つ最大秒数
ANSWER_TIMEOUT_SEC = 180.0

# 返答として読み上げない画面上の文字（ボタン名など）。完全一致で除外します。
UI_NOISE_LINES = [
    "Copy", "Retry", "Edit", "Share", "Good response", "Bad response",
    "コピー", "再試行", "編集", "共有", "良い回答", "悪い回答",
    "Claude can make mistakes. Please double-check responses.",
    "Claude は間違えることがあります。回答を再確認してください。",
    "Reply to Claude...", "Claudeに返信...",
]

# ---- 読み上げ -------------------------------------------------------------
# 読み上げ速度（Windows 標準は 200 前後）
TTS_RATE = 190
# 日本語音声を選ぶためのキーワード（声の名前に含まれる文字）
TTS_VOICE_KEYWORDS = ["Japanese", "Haruka", "Ayumi", "Sayaka", "Ichiro", "Nanami"]
# 読み上げる最大文字数（長すぎる返答は途中で切ります）
TTS_MAX_CHARS = 1500
# 起動時の返事（空文字にすると効果音だけ）
WAKE_REPLY = "はい"
