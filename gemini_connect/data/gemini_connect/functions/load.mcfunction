#> gemini_connect:load
# データパック読み込み時、または /reload 時に実行

# 念のため、Geminiの思考状態と応答をすべてリセットする
data remove storage gemini:io state
data remove storage gemini:io response

say "§a[Gemini Connect] AI state has been reset."