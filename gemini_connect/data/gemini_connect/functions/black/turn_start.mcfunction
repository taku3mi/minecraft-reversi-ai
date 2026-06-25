# ▼▼▼ [修正] 代わりに「強制リセット」処理を追加 ▼▼▼
data remove storage gemini:io state
data remove storage gemini:io response

# --- ▼▼▼ [追加] 黒（AI）の配置可能マス計算とNBT設定 ---
# 1. 前のターン（白）の情報をクリア
execute as @e[type=marker,tag=reversi_marker,tag=reversi_can_place_here] run tag @s remove reversi_can_place_here
execute as @e[type=marker,tag=reversi_marker] unless data entity @s {data:{can_reverse_direction:{nw:false,n:false,ne:false,w:false,e:false,sw:false,s:false,se:false}}} run data modify entity @s data.can_reverse_direction set value {nw:false,n:false,ne:false,w:false,e:false,sw:false,s:false,se:false}

# 2. 黒が置ける場所を計算 (これが data.can_reverse_direction を設定する)
execute as @e[type=marker,tag=reversi_marker,tag=!reversi_ignore_find_can_place] if data entity @s {data:{disc:"white"}} at @s run function yrfs_reversi:black/player/find_can_place/_

# 3. 計算結果（can_reverse_direction）に基づき、配置可能マーカーにタグを付与
execute as @e[type=marker,tag=reversi_marker,tag=!reversi_can_place_here] if data entity @s {data:{disc:""}} unless data entity @s {data:{can_reverse_direction:{nw:false,n:false,ne:false,w:false,e:false,sw:false,s:false,se:false}}} run tag @s add reversi_can_place_here
execute as @e[type=marker,tag=reversi_marker,tag=reversi_can_place_here] if data entity @s {data:{disc:"",can_reverse_direction:{nw:false,n:false,ne:false,w:false,e:false,sw:false,s:false,se:false}}} run tag @s remove reversi_can_place_here

# 4. もし置ける場所が一つもなければパス処理 (AIにリクエストを送らずにターン終了)
execute unless entity @e[type=marker,tag=reversi_can_place_here] run function yrfs_reversi:black/pass
execute unless entity @e[type=marker,tag=reversi_can_place_here] run return 0
# --- ▲▲▲ [追加] ここまで ---

# 思考中フラグを立てる
data modify storage gemini:io state set value "waiting"

# ▼▼▼ [今回追加する重要な修正] 合法手リスト(valid_moves)をストレージに保存 ▼▼▼
# Python側が読み取れるように、置ける場所の座標(Pos)をリストとして保存します
data modify storage gemini:io valid_moves set value []
execute as @e[type=marker,tag=reversi_can_place_here] run data modify storage gemini:io valid_moves append from entity @s Pos
# ▲▲▲ 追加ここまで ▲▲▲

# 1. 盤面情報をストレージに書き出す
function gemini_connect:common/read_board

# 2. 外部連携スクリプトへの通知
say "GEMINI_REQUEST: black"

# 3. Geminiからの応答を待機するループを開始
schedule function gemini_connect:black/wait_for_response 1s replace