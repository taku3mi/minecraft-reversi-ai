#> gemini_connect:white/turn_start

# ▼▼▼ [修正] 以下の「多重起動防止チェック」を削除 ▼▼▼
# execute if data storage gemini:io state run return 0
# execute if data storage gemini:io response.pos run return 0

# ▼▼▼ [修正] 代わりに「強制リセット」処理を追加 ▼▼▼
data remove storage gemini:io state
data remove storage gemini:io response

# 思考中フラグを立てる
data modify storage gemini:io state set value "waiting"

# 1. 盤面情報をストレージに書き出す（共通関数を呼び出し）
function gemini_connect:common/read_board

# 2. 外部連携スクリプトへの通知
say "GEMINI_REQUEST: white"

# 3. Geminiからの応答を待機するループを開始
schedule function gemini_connect:white/wait_for_response 1s replace