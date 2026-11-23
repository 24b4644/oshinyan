@echo off
chcp 65001 > nul
cd /d %~dp0

echo [1/3] Python の仮想環境を作成します...
py -3 -m venv .venv || python -m venv .venv
if errorlevel 1 (
  echo Python が見つかりません。https://www.python.org/ からインストールしてください。
  pause & exit /b 1
)

echo [2/3] ライブラリをインストールします...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 ( pause & exit /b 1 )

echo [3/3] 日本語の音声認識モデル（約50MB）をダウンロードします...
if exist model (
  echo model フォルダは既にあります。スキップします。
) else (
  powershell -NoProfile -Command ^
    "Invoke-WebRequest https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip -OutFile model.zip; Expand-Archive model.zip -DestinationPath .; Rename-Item vosk-model-small-ja-0.22 model; Remove-Item model.zip"
)

echo.
echo セットアップ完了！ run.bat で起動してください。
pause
