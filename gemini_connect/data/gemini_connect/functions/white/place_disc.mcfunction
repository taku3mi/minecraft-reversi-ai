#> gemini_connect:white/place_disc

# ▼▼▼ [修正] 状態を "placing" （配置中）に変更 ▼▼▼
data modify storage gemini:io state set value "placing"

# 1. Geminiが指定した座標からマーカーを特定
data modify storage yrfs_reversi: root.temp.pos set from storage gemini:io response.pos
function gemini_connect:common/find_marker_by_pos

# 2. 該当マーカーで石を置く処理を実行
execute as @e[type=marker,tag=reversi_marker,tag=gemini_target] at @s if data storage yrfs_reversi: {root:{game_status:{turn:"white"}}} run function yrfs_reversi:white/rotation/init

# 3. 後処理
tag @e[type=marker,tag=gemini_target] remove gemini_target

# ▼▼▼ [修正] 応答(response) と 状態(state) の両方を必ず削除する ▼▼▼
data remove storage gemini:io response
data remove storage gemini:io state