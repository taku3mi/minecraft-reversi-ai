# Minecraft Reversi AI — Gemini対戦

MinecraftのオセロゲームにGemini AIを組み込んだデータパックです。  
プレイヤーはMinecraft内の8×8ボードでAI（Gemini）とオセロ対決できます。

## 構成

```
datapacks/
├── Reversi/              # オセロゲームのデータパック（ボード管理・ゲームロジック）
├── gemini_connect/       # Gemini AI連携用データパック（AIターン制御）
├── gemini_connector.py   # Python RCONブリッジスクリプト
├── requirements.txt      # Python依存パッケージ
├── .env.example          # 環境変数テンプレート
└── README.md
```

## セットアップ

### 1. Minecraftサーバーの準備

`server.properties` でRCONを有効化してください：

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_password_here
```

データパック `Reversi/` と `gemini_connect/` をワールドの `datapacks/` フォルダに配置し、  
サーバーを起動後に `/reload` を実行してください。

### 2. Pythonセットアップ

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、値を入力してください：

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_gemini_api_key_here   # Google AI Studio で取得
RCON_PASSWORD=your_rcon_password_here      # server.properties の rcon.password と同じ値
RCON_HOST=127.0.0.1
RCON_PORT=25575
LOG_FILE_PATH=/path/to/your/minecraft/logs/latest.log
```

### 4. スクリプトを起動

Minecraftサーバーが起動している状態で実行してください：

```bash
python3 gemini_connector.py
```

`[情報] RCON接続成功` と表示されれば準備完了です。

## 遊び方

1. Minecraftサーバーに接続する
2. オセロゲームを開始する（`gemini_connect` データパックの指示に従う）
3. AIのターン（黒）になると `gemini_connector.py` が自動的にGeminiへ思考を依頼し、着手します

## 動作の仕組み

```
Minecraft (ゲームロジック)
  └─ AIターン開始 → ログに "GEMINI_REQUEST: black" を出力
       ↓
gemini_connector.py (RCONで監視)
  └─ 盤面・合法手をMinecraftストレージから取得
  └─ Gemini APIへプロンプト送信
  └─ 着手座標をMinecraftストレージへ書き込み
       ↓
Minecraft (着手処理)
  └─ ストレージの座標を読んでディスクを配置
```

## 必要なもの

- Minecraft Java Edition（サーバー）
- Python 3.10+
- Gemini API キー（[Google AI Studio](https://aistudio.google.com/) で無料取得可能）
