#> gemini_connect:black/place_disc

# 状態を "placing" （配置中）に変更
data modify storage gemini:io state set value "placing"

# 1. Geminiが指定した座標からマーカーを特定
data modify storage yrfs_reversi: root.temp.pos set from storage gemini:io response.pos
function gemini_connect:common/find_marker_by_pos

# --- ▼▼▼ [追加] AIの着手チェックとフォールバック ---
# 2a. AIが不正な手（配置可能マス以外）を選んだかチェック
execute if entity @e[type=marker,tag=reversi_marker,tag=gemini_target,limit=1,tag=!reversi_can_place_here] run function gemini_connect:black/invalid_move

# 2b. 該当マーカー（AIが選んだ正規の手、または invalid_move で選び直された手）で石を置く処理を実行
execute as @e[type=marker,tag=reversi_marker,tag=gemini_target,limit=1,tag=reversi_can_place_here] at @s run function yrfs_reversi:black/rotation/init
# --- ▲▲▲ [変更] 元の execute コマンドは上記 2b に置き換え ---

# 3. 後処理
tag @e[type=marker,tag=gemini_target] remove gemini_target

# [修正] 応答(response) と 状態(state) の両方を必ず削除する
data remove storage gemini:io response
data remove storage gemini:io state