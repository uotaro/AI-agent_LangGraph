# common_utils.py
# 01_chatbot.py と 02_chatbot_tools.py で使用する共通のユーティリティ関数を定義するファイル
# 01_chatbot.py と 02_chatbot_tools.py の両方で、Graphの実行結果を整形して表示するための関数 format_result() を定義

import json

def message_to_dict(msg):
    """メッセージオブジェクトをシリアライズ可能な辞書形式に変換する関数"""
    if hasattr(msg, "dict"):
        d = msg.dict()
        msg_type = d.get("type")
        
        # 基本構造の作成
        result_dict = {
            "type": msg_type,
            "content": d.get("content")
        }
        
        # パターン1: AIMessageが「ツール呼び出し」を要求している場合
        if msg_type == "ai" and d.get("tool_calls"):
            result_dict["tool_calls"] = [
                {
                    "name": tc.get("name"),
                    "args": tc.get("args"),
                    "id": tc.get("id")
                }
                for tc in d.get("tool_calls")
            ]
            
        # パターン2: ToolMessage（ツールの実行結果）の場合
        elif msg_type == "tool":
            result_dict["name"] = d.get("name")
            result_dict["tool_call_id"] = d.get("tool_call_id")
            
        return result_dict
        
    return str(msg)

def format_result(result):
    """result の中身（messagesリスト）を整形する関数

    Args:
        result (dict): Graphの実行結果。通常は{"messages": [...] }の形式
    
    Returns:
        str: 整形された結果のJSON文字列
    """
    # print("=== raw_result ここから ===")
    # print(result)
    # print("=== raw_result ここまで ===")
    # result の中身（messagesリスト）を整形
    formatted_messages = [message_to_dict(msg) for msg in result["messages"]]
    formatted_result = {"messages": formatted_messages}
    return json.dumps(formatted_result, indent=4, ensure_ascii=False)
