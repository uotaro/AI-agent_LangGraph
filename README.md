# AI-agent_LangGraph
AIエージェントのお勉強：LangGraphフレームワークを使ってみる

### 参考URL：
- [【初心者向け】LangGraphの紹介と基本的な使い方 #初心者 - Qiita](https://qiita.com/sakuraia/items/27db3f118e0ee41c54c1)
- [LangGraph 公式ドキュメント](https://docs.langchain.com/oss/python/langgraph/overview)
- [Workflows and agents - Docs by LangChain](https://docs.langchain.com/oss/python/langgraph/workflows-agents)

## 必要なモジュール類

```bash
pip install langchain langchain-openai langgraph dotenv grandalf
```

### 01_chatbot.py
LangGraph を使用してチャットボットを作成するシンプルなサンプルコード

### 02_chatbot_tools.py
01_chatbot.pyで作成したチャットボットにツール呼び出し機能を追加するサンプルコード

### common_utils.py
01_chatbot.py と 02_chatbot_tools.py の両方で、Graphの実行結果を整形して表示するための関数 format_result() を定義

