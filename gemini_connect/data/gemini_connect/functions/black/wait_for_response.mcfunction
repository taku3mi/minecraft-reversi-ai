#> gemini_connect:black/wait_for_response

# --- ▼▼▼ デバッグ追加 ▼▼▼ ---
say (wait) 応答チェックを開始

# 1. state の確認
execute if data storage gemini:io {state:"waiting"} run say (wait) stateは "waiting" です。
execute unless data storage gemini:io {state:"waiting"} run say (wait) エラー：stateが "waiting" ではありません。

# 2. response.pos の確認
execute if data storage gemini:io response.pos run say (wait) response.pos が見つかりました！
execute unless data storage gemini:io response.pos run say (wait) ...response.pos がまだありません。
# --- ▲▲▲ デバッグ追加 ▲▲▲ ---


# 3. 応答があれば place_disc を実行
execute if data storage gemini:io {state:"waiting"} if data storage gemini:io response.pos run function gemini_connect:black/place_disc

# 4. 応答がなければ再スケジュール
execute if data storage gemini:io {state:"waiting"} unless data storage gemini:io response.pos run schedule function gemini_connect:black/wait_for_response 1s replace

# 5. ▼▼▼ [修正] 再スケジュールが実行されたかログを追加 ▼▼▼
execute if data storage gemini:io {state:"waiting"} unless data storage gemini:io response.pos run say (wait) 1秒後に再スケジュールしました。