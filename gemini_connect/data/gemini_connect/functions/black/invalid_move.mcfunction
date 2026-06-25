#> gemini_connect:black/invalid_move
# AIが不正な手（配置可能マス以外）を選択した場合のフォールバック処理



# 1. 現在のターゲット（不正なマス）からタグを剥がす
tag @e[type=marker,tag=reversi_marker,tag=gemini_target] remove gemini_target

# 2. 配置可能なマス（reversi_can_place_here）からランダムに1つ選び、新しいターゲットにする
tag @e[type=marker,tag=reversi_marker,tag=reversi_can_place_here,sort=random,limit=1] add gemini_target