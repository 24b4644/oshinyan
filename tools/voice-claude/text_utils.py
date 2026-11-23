"""OS に依存しない文字処理（ウェイクワード判定・返答の抽出・読み上げ用の整形）。"""
import re
import unicodedata

_SMALL_KANA = str.maketrans("ァィゥェォッャュョヮ", "アイウエオツヤユヨワ")
_PUNCT_RE = re.compile(r"[\s、。,.!?！？「」『』（）()・…~〜ー-]")


def to_katakana(text: str) -> str:
    """ひらがなをカタカナに変換する。"""
    return "".join(
        chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in text
    )


def normalize(text: str) -> str:
    """比較用に正規化する（全角半角の統一・カタカナ化・記号と空白と長音の除去）。"""
    text = unicodedata.normalize("NFKC", text)
    text = to_katakana(text).translate(_SMALL_KANA)
    return _PUNCT_RE.sub("", text)


def is_wake_word(text: str, patterns, loose_patterns=(), loose=False) -> bool:
    """認識結果にウェイクワードが含まれるか判定する。"""
    norm = normalize(text)
    if not norm:
        return False
    targets = list(patterns) + (list(loose_patterns) if loose else [])
    return any(normalize(p) in norm for p in targets)


def extract_answer(screen_text: str, question: str, noise_lines=()) -> str:
    """画面全体の文字から、最後に送った質問より後ろの部分（＝返答）を取り出す。"""
    lines = [ln.strip() for ln in screen_text.splitlines()]
    lines = [ln for ln in lines if ln]
    q = normalize(question)
    key = q[:20]
    idx = -1
    if key:
        for i in range(len(lines) - 1, -1, -1):
            n = normalize(lines[i])
            if n and (key in n or (len(n) >= 4 and n in q)):
                idx = i
                break
    if idx < 0:
        return ""
    noise = {normalize(x) for x in noise_lines}
    out = []
    for ln in lines[idx + 1:]:
        if normalize(ln) in noise:
            continue
        if out and ln == out[-1]:
            continue  # 同じ文字が二重に取れた場合
        out.append(ln)
    return "\n".join(out)


_CODE_BLOCK_RE = re.compile(r"```.*?(```|$)", re.S)
_URL_RE = re.compile(r"https?://\S+")


def clean_for_tts(text: str, max_chars: int = 1500) -> str:
    """読み上げに向かない記号やコードを取り除く。"""
    text = _CODE_BLOCK_RE.sub("（コードは画面で確認してください）", text)
    text = _URL_RE.sub("（リンク）", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)      # 見出し
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)            # 箇条書き
    text = re.sub(r"^\s*\|?[-:| ]{3,}\|?\s*$", "", text, flags=re.M)  # 表の区切り
    text = text.replace("|", "、")
    text = re.sub(r"[*_~>#]", "", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "。以下は画面で確認してください。"
    return text
