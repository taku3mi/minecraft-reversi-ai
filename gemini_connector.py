import time
import re
import json
import os
from mcrcon import MCRcon
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- 1. 設定 ---
RCON_HOST = os.environ.get("RCON_HOST", "127.0.0.1")
RCON_PORT = int(os.environ.get("RCON_PORT", "25575"))
RCON_PASSWORD = os.environ.get("RCON_PASSWORD", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
LOG_FILE_PATH = os.environ.get("LOG_FILE_PATH", "logs/latest.log")
GEMINI_MODEL = "gemini-2.5-flash-lite-preview-06-17"

# --- 2. Gemini APIの設定 ---
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- 3. ヘルパー関数 ---

def send_rcon_command(mcr, command):
    """RCONでコマンドを送信し、応答を取得する"""
    try:
        resp = mcr.command(command)
        return resp
    except Exception as e:
        print(f"[エラー] RCONコマンド送信失敗: {e}")
        try:
            print("[情報] RCON再接続中...")
            mcr.connect()
            return mcr.command(command)
        except Exception as e2:
            print(f"[エラー] RCON再接続失敗: {e2}")
            return None

def parse_nbt_data(rcon_output):
    """RCONのNBT形式の応答をPythonリストに変換する"""
    try:
        # "Storage gemini:io has the following contents: [ ... ]" みたいな形式から [] の中身を抽出
        match = re.search(r"(\[.*\])", rcon_output, re.DOTALL)
        if not match:
            return None
        
        json_str = match.group(1)
        # MinecraftのNBT表記をJSONに近づける
        # 数値の直後にあるd, f, bサフィックスのみを削除（文字列内の文字は保護）
        json_str = re.sub(r'(\d+\.?\d*)[dfb]', r'\1', json_str)
        json_str = json_str.replace("'", '"')
        
        return json.loads(json_str)
    except Exception as e:
        print(f"[エラー] データパース失敗: {e}")
        return None

def find_closest_grid(x, z):
    """Minecraft座標を 0-7 のグリッドインデックス(row, col)に変換"""
    # 盤面の定義座標 (x_coords[i], z_coords[j])
    # Minecraft: X=-3.5(Row 0) ... +3.5(Row 7)
    # Minecraft: Z=-3.5(Col 0) ... +3.5(Col 7)
    
    row = int((x + 4.0)) # -3.5 -> 0.5 -> int(0)
    col = int((z + 4.0)) 
    
    # 範囲チェック
    row = max(0, min(7, row))
    col = max(0, min(7, col))
    
    return row, col

def get_valid_moves_from_storage(mcr):
    """Minecraftから合法手リスト(valid_moves)を取得し、グリッド座標に変換する"""
    resp = send_rcon_command(mcr, "data get storage gemini:io valid_moves")
    if not resp:
        return []
    
    coords_list = parse_nbt_data(resp)
    if not coords_list:
        return []

    print(f"[デバッグ] Minecraftから取得した座標: {coords_list}")

    valid_moves = []
    # coords_list は [[x, y, z], [x, y, z], ...] の形式
    for pos in coords_list:
        if len(pos) >= 3:
            x, _, z = pos
            r, c = find_closest_grid(x, z)
            print(f"[デバッグ] 座標変換: MC({x}, {z}) → Grid(row={r}, col={c}) → 棋譜{chr(ord('a')+c)}{r+1}")
            valid_moves.append((r, c))
            
    return valid_moves

def format_board_for_gemini(board_list, player_color, valid_moves):
    """Geminiへのプロンプト作成"""
    board_str = "  a b c d e f g h\n"
    symbol_map = {"": ".", "black": "B", "white": "W"}
    
    # valid_moves をセットに変換（検索用）
    valid_set = set(valid_moves)

    for i in range(8): # Row (X)
        row_str = f"{i+1} "
        for j in range(8): # Col (Z)
            # read_board の順序は Row-major (X then Z) なのでそのまま使える
            index = i * 8 + j 
            cell_content = board_list[index] if index < len(board_list) else ""
            cell = symbol_map.get(cell_content, "?")
            
            # 合法手なら * で強調（ただし空きマスの場合のみ）
            if (i, j) in valid_set and cell_content == "":
                cell = "*"
            
            row_str += cell + " "
        board_str += row_str + "\n"
    
    # 棋譜形式のリスト
    move_str_list = []
    for r, c in valid_moves:
        # Row(0-7) -> 1-8, Col(0-7) -> a-h
        coord_str = f"{chr(ord('a') + c)}{r + 1}"
        move_str_list.append(coord_str)

    prompt = (
        f"現在の盤面:\n{board_str}\n"
        f"あなたは「{player_color}」(記号: {symbol_map[player_color]})です。\n"
        f"置ける場所(*): {', '.join(move_str_list)}\n\n"
        f"このリストの中から、戦略的に最も有利な手を1つ選び、座標(例: d3)のみを答えてください。"
    )
    return prompt

def parse_gemini_response(response_text, valid_moves):
    """Geminiの応答を解析し、Minecraft座標(X, Z)を返す"""
    response_text = response_text.strip().lower()
    match = re.search(r"([a-h])([1-8])", response_text)
    
    if not match:
        print(f"[警告] 形式不明な応答: {response_text}")
        return None
        
    col_char, row_char = match.groups()
    c = ord(col_char) - ord('a')
    r = int(row_char) - 1
    
    print(f"[デバッグ] AIの選択: {col_char}{row_char} → (row={r}, col={c})")
    print(f"[デバッグ] valid_movesに含まれているか: {(r, c) in valid_moves}")
    
    # AIが選んだ手が合法手リストにあるか確認
    if (r, c) not in valid_moves:
        print(f"[警告] AIがリストにない手 {col_char}{row_char} を選択しました。")
        # リストにある最初の手をフォールバックとして使う
        if valid_moves:
            r, c = valid_moves[0]
            print(f"[修正] 強制的に {chr(ord('a')+c)}{r+1} を選択します。")
        else:
            return None # 合法手がそもそもない場合（通常ありえない）

    # グリッド(r, c) -> Minecraft座標(X, Z)
    # X = -3.5 + r
    # Z = -3.5 + c
    mc_x = -3.5 + r
    mc_z = -3.5 + c
    
    return [mc_x, mc_z]

# --- 4. メインループ ---

def follow_log(filepath):
    if not os.path.exists(filepath):
        print(f"[エラー] ログなし: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as file:
        file.seek(0, 2)
        print(f"[情報] 監視開始: {filepath}")
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

def main():
    mcr = MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT)
    try:
        mcr.connect()
        print("[情報] RCON接続成功")
    except Exception as e:
        print(f"[エラー] RCON接続失敗: {e}")
        return

    try:
        for line in follow_log(LOG_FILE_PATH):
            if "GEMINI_REQUEST: black" in line:
                print("\n[検知] 黒(AI)のターン")
                
                # 1. 盤面取得
                resp_board = send_rcon_command(mcr, "data get storage gemini:io board")
                board_list = parse_nbt_data(resp_board)
                
                print(f"[デバッグ] 盤面データ: {board_list[:16] if board_list else None}...")  # 最初の2行だけ表示
                
                # 2. 合法手リスト取得 (Minecraftが計算したもの)
                valid_moves = get_valid_moves_from_storage(mcr)
                
                if not board_list or not valid_moves:
                    print("[エラー] データ取得失敗")
                    continue
                    
                print(f"[情報] Minecraft提示の合法手: {len(valid_moves)}手")
                print(f"[デバッグ] 合法手リスト (row, col): {valid_moves}")
                
                # 合法手を棋譜形式で表示
                move_str_list = []
                for r, c in valid_moves:
                    coord_str = f"{chr(ord('a') + c)}{r + 1}"
                    move_str_list.append(coord_str)
                print(f"[デバッグ] 合法手リスト (棋譜): {', '.join(move_str_list)}")

                # 3. Gemini思考
                prompt = format_board_for_gemini(board_list, "black", valid_moves)
                print(f"[デバッグ] Geminiへのプロンプト:\n{prompt}\n")
                try:
                    gemini_resp = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt).text
                    print(f"[AI] 思考結果: {gemini_resp}")
                except Exception as e:
                    print(f"[エラー] APIエラー: {e}")
                    continue

                # 4. 座標変換と送信
                target_pos = parse_gemini_response(gemini_resp, valid_moves)
                if target_pos:
                    x, z = target_pos
                    cmd = f"data modify storage gemini:io response.pos set value [{x}d, {z}d]"
                    send_rcon_command(mcr, cmd)
                    print(f"[完了] {x}, {z} に着手")

    finally:
        mcr.disconnect()

if __name__ == "__main__":
    main()
