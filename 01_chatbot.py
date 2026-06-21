# 01_chatbot.py
# LangGraph を使用してチャットボットを作成するシンプルなサンプルコード
import os
from dotenv import load_dotenv
from typing import TypedDict
from typing import Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from common_utils import format_result

# .envファイルから環境変数を読み込む
load_dotenv()

use_local_llm = True  # True: LAN内の llama.cpp APIサーバーを使用する, False: Google Gemini APIを使用する

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
# Stateの定義
#===================================================================
class State(TypedDict):
    messages: Annotated[list, add_messages]

#===================================================================
# Nodeの定義
# LangGraph では Node の処理を関数として定義する。
#===================================================================
def chatbot(state: State):
    # LLMが生成した回答でStateを更新
    return {"messages": [llm.invoke(state["messages"])]}

#===================================================================
# Graphの初期化
# StateGraphクラスにStateを渡して、Graphのインスタンスを生成
#===================================================================
graph_builder = StateGraph(State)

#===================================================================
# Nodeの追加
# add_node関数の第1引数にはNode名、第2引数には関数名を設定.
# 第1引数に設定されたNode名はEdgeの設定の際に使用する
#===================================================================
graph_builder.add_node("chatbot", chatbot)

#===================================================================
# Node間を接続するEdgeの追加
# add_edge関数の第1引数には遷移元のNode名を設定し、第2引数には遷移先のNode名を設定
# STARTは始点NodeをENDは終点Nodeを表す特殊なNode
#===================================================================
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

#===================================================================
# Graphのコンパイル
# invoke関数に初期状態を渡して実行すると、Graph内のすべての処理が実行された後の最終結果が返される
#===================================================================
graph = graph_builder.compile()

# グラフ構造の可視化
print(graph.get_graph().print_ascii())

#===================================================================
# Graphの実行
#===================================================================
result = graph.invoke({"messages": ["こんにちは"]})

#===================================================================
# 結果表示
#===================================================================
# 結果全体を出力したい場合
print(format_result(result))

# チャットボットの回答のみ出力したい場合
# print(result["messages"][-1].content)
