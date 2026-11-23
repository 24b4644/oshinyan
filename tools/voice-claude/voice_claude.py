"""「ねぇ、クロード」で Claude デスクトップアプリを呼び出し、返答を読み上げる常駐ツール（Windows）。

使い方: run.bat をダブルクリック（終了は Ctrl+C）
"""
import ctypes
import json
import os
import queue
import sys
import time

import numpy as np
import pyttsx3
import sounddevice as sd
import speech_recognition as sr
import winsound
from vosk import KaldiRecognizer, Model, SetLogLevel

import config
from claude_window import ClaudeWindow
from text_utils import clean_for_tts, is_wake_word

BLOCK = int(config.SAMPLE_RATE * 0.1)  # 0.1 秒ごとに音声を受け取る


# ---- 読み上げ ---------------------------------------------------------------
class Speaker:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", config.TTS_RATE)
        for v in self.engine.getProperty("voices"):
            label = f"{v.name} {v.id}"
            if any(k.lower() in label.lower() for k in config.TTS_VOICE_KEYWORDS):
                self.engine.setProperty("voice", v.id)
                print(f"[読み上げ音声] {v.name}")
                break
        else:
            print("[注意] 日本語の音声が見つかりません。Windows の設定 > 時刻と言語 > "
                  "音声認識 から日本語の音声を追加してください。")

    def say(self, text):
        if not text:
            return
        self.engine.say(text)
        self.engine.runAndWait()


# ---- マイク -----------------------------------------------------------------
class Mic:
    def __init__(self):
        self.q = queue.Queue()
        self.stream = sd.RawInputStream(
            samplerate=config.SAMPLE_RATE, blocksize=BLOCK, dtype="int16",
            channels=1, callback=self._cb)

    def _cb(self, indata, frames, t, status):
        self.q.put(bytes(indata))

    def start(self):
        self.stream.start()

    def read(self, timeout=1.0):
        return self.q.get(timeout=timeout)

    def drain(self):
        """読み上げ中などに溜まった音声を捨てる（自分の声で反応しないように）。"""
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break


def rms(chunk: bytes) -> float:
    a = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
    return float(np.sqrt(np.mean(a * a))) if a.size else 0.0


def calibrate(mic: Mic, seconds=1.5) -> float:
    if config.SPEECH_RMS_THRESHOLD:
        return float(config.SPEECH_RMS_THRESHOLD)
    vals = [rms(mic.read()) for _ in range(int(seconds / 0.1))]
    th = max(300.0, float(np.mean(vals)) * 3.0)
    print(f"[マイク] 周囲の音量 {np.mean(vals):.0f} → 話し声のしきい値 {th:.0f}")
    return th


def record_question(mic: Mic, threshold: float) -> bytes:
    """話し始めを待ち、無音が続いたら録音を終える。"""
    mic.drain()
    frames, started = [], False
    silent = 0.0
    t0 = time.time()
    while True:
        chunk = mic.read()
        loud = rms(chunk) >= threshold
        if not started:
            if loud:
                started = True
                frames.append(chunk)
            elif time.time() - t0 > config.WAIT_FOR_SPEECH_SEC:
                return b""
            continue
        frames.append(chunk)
        silent = 0.0 if loud else silent + 0.1
        if silent >= config.END_SILENCE_SEC or \
                len(frames) * 0.1 >= config.MAX_QUESTION_SEC:
            return b"".join(frames)


def transcribe(audio: bytes, model: Model) -> str:
    if not audio:
        return ""
    if config.QUESTION_STT == "google":
        try:
            data = sr.AudioData(audio, config.SAMPLE_RATE, 2)
            return sr.Recognizer().recognize_google(data, language="ja-JP")
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"[注意] Google 音声認識に接続できません（{e}）。Vosk で認識します。")
    rec = KaldiRecognizer(model, config.SAMPLE_RATE)
    rec.AcceptWaveform(audio)
    return json.loads(rec.FinalResult()).get("text", "").replace(" ", "")


# ---- メイン -----------------------------------------------------------------
def main():
    if os.name == "nt":
        ctypes.windll.kernel32.SetConsoleTitleW("Voice Launcher")
    if not os.path.isdir(config.VOSK_MODEL_DIR):
        sys.exit(f"Vosk モデルがありません: {config.VOSK_MODEL_DIR}\n"
                 "先に setup.bat を実行してください。")

    SetLogLevel(-1)
    model = Model(config.VOSK_MODEL_DIR)
    speaker = Speaker()
    claude = ClaudeWindow()
    mic = Mic()
    mic.start()
    threshold = calibrate(mic)

    def new_wake_recognizer():
        return KaldiRecognizer(model, config.SAMPLE_RATE)

    wake_rec = new_wake_recognizer()
    print("\n待機中…「ねぇ、クロード」と呼びかけてください（終了: Ctrl+C）\n")

    while True:
        try:
            chunk = mic.read()
        except queue.Empty:
            continue

        is_final = wake_rec.AcceptWaveform(chunk)
        if is_final:
            heard = json.loads(wake_rec.Result()).get("text", "")
        else:
            heard = json.loads(wake_rec.PartialResult()).get("partial", "")
        if not heard:
            continue
        if not is_wake_word(heard, config.WAKE_PATTERNS,
                            config.LOOSE_PATTERNS, config.WAKE_LOOSE):
            if is_final:
                # 反応しないときは、ここに出る文字を config.py の WAKE_PATTERNS に追加
                print(f"[聞こえた] {heard.replace(' ', '')}")
            continue

        # ---- ウェイクワード検知 ----
        print(f"[聞こえた] {heard}  → 起動")
        wake_rec = new_wake_recognizer()
        try:
            claude.bring_to_front()
        except Exception as e:
            print(f"[エラー] {e}")
            speaker.say("クロードのアプリを開けませんでした")
            mic.drain()
            continue
        winsound.Beep(880, 150)
        speaker.say(config.WAKE_REPLY)

        print("[録音中] 質問をどうぞ…")
        audio = record_question(mic, threshold)
        question = transcribe(audio, model)
        if not question:
            print("[録音] 聞き取れませんでした")
            speaker.say("聞き取れませんでした")
            mic.drain()
            continue
        print(f"[質問] {question}")
        winsound.Beep(660, 120)

        try:
            claude.send(question)
            print("[送信] 返答を待っています…")
            answer = claude.wait_answer(
                question, on_progress=lambda n: print(f"\r[受信中] {n} 文字", end=""))
            print()
        except Exception as e:
            print(f"[エラー] {e}")
            answer = ""

        if answer:
            print(f"[返答]\n{answer}\n")
            speaker.say(clean_for_tts(answer, config.TTS_MAX_CHARS))
        else:
            speaker.say("返答を読み取れませんでした。画面で確認してください")
        mic.drain()
        print("待機中…")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n終了しました。")
