# 02_chatbot_tools.py
# 01_chatbot.pyで作成したチャットボットにツール呼び出し機能を追加するサンプルコード
import os
from dotenv import load_dotenv
from typing import TypedDict
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from common_utils import format_result

# .envファイルから環境変数を読み込む
load_dotenv()

use_local_llm = False  # True: LAN内の llama.cpp APIサーバーを使用する, False: Google Gemini APIを使用する

#===================================================================
# tool の定義
# LLMから呼び出される関数を定義する。
# @toolデコレータを使用して関数を定義することでLLMから呼び出される関数を作成することができる。
#===================================================================
@tool
def multiply_function(x: int, y: int) -> int:
    """
    2つのint型の値を引数で受け取り、掛け算の結果をint型で返す

    Args:
        x (int): 1つ目のint型の引数
        y (int): 2つ目のint型の引数

    Returns:
        int: x * y
    """
    return x * y

@tool
def add_function(x: int, y: int) -> int:
   """
    2つのint型の値を引数で受け取り、足し算の結果をint型で返す

    Args:
        x (int): 1つ目のint型の引数
        y (int): 2つ目のint型の引数

    Returns:
        int: x + y
    """
   return x + y

#===================================================================
# ツールの辞書作成
#===================================================================
tools_dict = {
    "multiply_function": multiply_function,
    "add_function": add_function
}

#===================================================================
# モデル設定
#===================================================================
if use_local_llm:
    llm = ChatOpenAI(
        base_url="http://localhost:8080/v1",
        api_key=os.getenv("LLAMA_API_TOKEN"),
        model="local-model",                  # Llama.cpp側でモデル名が未指定でも、何か文字列を入れないとエラーになる場合があるため、適当な文字列を入れている
        temperature=0.7
    )
else:
    llm = ChatOpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model="gemini-2.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.7
    )

#===================================================================
# tools の作成
#===================================================================
tools = [multiply_function, add_function]

# tools をモデルに紐づけ
llm_with_tools = llm.bind_tools(tools)

#===================================================================
# State の定義
#===================================================================
class State(TypedDict):
    messages: Annotated[list, add_messages]

#===================================================================
# Node の定義
#===================================================================
# chatbot の Node を定義
def chatbot(state: State):
    # LLMに対して「ツールを使うこと」を強く指示するシステムプロンプト
    system_prompt = SystemMessage(
        content="あなたは計算のプロフェッショナルです。計算を行う際は、自分で計算せず、必ず提供されたツール（multiply_function または add_function）を呼び出して実行してください。自力で計算してはいけません。"
    )
    # Stateの過去のメッセージ一覧の先頭にシステムプロンプトを結合してLLMに渡す
    inputs = [system_prompt] + state["messages"]
    # LLMが有効なtoolを選択して生成した回答でStateを更新
    result = llm_with_tools.invoke(inputs)
    # 戻り値はStateクラスの辞書型に合わせるため、key=messages、value=invoke関数の出力結果をリスト型で返す
    return {"messages": [result]}

# tool の Node を定義
def tool(state: State):
    # 最後のメッセージを取得
    last_message = state["messages"][-1]
    # 実行結果を保存するためのリスト
    messages = []
    for tool_call in last_message.tool_calls:
        # toolの実行
        tool_output = tools_dict[tool_call["name"]].invoke(tool_call["args"])
        # toolの結果を使用してToolMessageの作成
        tool_messages = ToolMessage(
            content=tool_output,           # ツールの実行結果
            name=tool_call["name"],        # ツールの名前
            tool_call_id=tool_call["id"],  # ツール呼び出しのID
        )
        # ToolMessageをmessagesリストに追加
        messages.append(tool_messages)
    # Stateを更新可能な辞書型を返す. Stateクラスの辞書型に合わせるため、key=messages、value=messagesリストを設定して返す
    return {"messages": messages}

#===================================================================
# 条件分岐を判断する router 関数を定義
#===================================================================
def router(state: State):
    # 最後のメッセージを取得
    last_message = state["messages"][-1]
    # 最後のメッセージに tool_calls が存在するか判定
    if last_message.tool_calls:
        # tool_calls が存在する場合、"tool" を返す
        return "tool"
    else:
        # それ以外の場合、"end" を返す
        return "end"

#===================================================================
# Graphの初期化
#===================================================================
graph_builder = StateGraph(State)

# chatbot Node の追加
graph_builder.add_node("chatbot", chatbot)
# tool Node の追加
graph_builder.add_node("tool", tool)

# 条件付き Edge の追加
graph_builder.add_conditional_edges(
    # 遷移元の Node 名を設定
    "chatbot",
    # 条件分岐を判断する関数を設定
    router,
    # router の戻り値によって遷移先の Node を決める
    {
        # "tool"の場合、tool Node に遷移
        "tool": "tool",
        #"end"の場合、END Node に遷移
        "end": END
    }
)

# tool Node から chatbot Node への Edge を追加
graph_builder.add_edge("tool", "chatbot")
# START から chatbot Node への Edge を追加
graph_builder.add_edge(START, "chatbot")

#===================================================================
# Graphのコンパイル
#===================================================================
graph = graph_builder.compile()

# グラフ構造の可視化
print(graph.get_graph().print_ascii())

#===================================================================
# Graphの実行
#===================================================================

mssage_items = [
    { "content": "100掛ける200の計算と1足す2の計算をそれぞれしてください。",  "description": "チャットボットが multiply_function と add_function 両方を呼び出すパターン" },
    { "content": "100掛ける200の計算をしてください",                        "description": "チャットボットが multiply_function のみ呼び出すパターン" },
    { "content": "1足す2の計算をしてください",                             "description": "チャットボットが add_function のみ呼び出すパターン" },
    { "content": "こんにちは",                                            "description": "チャットボットがツールを呼び出さないパターン" },
]

for item in mssage_items:
    print(f"\n--- ユーザーの入力: {item['content']} ---  {item['description']}")   
    result = graph.invoke({"messages": [item['content']]})
    #===================================================================
    # 結果表示
    #===================================================================
    # 結果全体を出力したい場合
    print(format_result(result))
    # # チャットボットの回答のみ出力したい場合
    # print(result["messages"][-1].content)
