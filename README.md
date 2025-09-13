# LangChain FastAPI 負荷テストプロジェクト

このプロジェクトは、LangChainとFastAPIで構築されたRAG（Retrieval-Augmented Generation）機能を持つストリーミングAPIの負荷テストをLocustで実行するためのものです。

## 🚀 機能

- **FastAPI + LangChain API**: RAG機能を持つストリーミングエンドポイント
- **Azure OpenAI統合**: GPT-4と埋め込みモデルの利用
- **Locust負荷テスト**: パフォーマンス測定
- **ストリーミング対応**: リアルタイムレスポンス
- **Docker対応**: 簡単なデプロイメント

## 📋 前提条件

- Python 3.11以上
- Azure OpenAI リソース
- Docker & Docker Compose（オプション）

## 🛠️ セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd langchain
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`env.example`をコピーして`.env`ファイルを作成し、Azure OpenAIの設定を行います：

```bash
cp env.example .env
```

`.env`ファイルを編集：

```env
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt-4-deployment-name
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment-name
```

### 4. Azure OpenAI設定のテスト

```bash
python azure_config.py
```

## 🚀 実行方法

`start.sh`スクリプトを使用すると、APIサーバーの起動や負荷テストの実行を簡単に行えます。

```bash
./start.sh
```

スクリプトを実行すると、以下のオプションが選択できます。

1.  **APIサーバーのみ起動**: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 8` を実行してAPIサーバーを起動します。
2.  **負荷テストを実行**: 対話形式で同時ユーザー数、生成レート、実行時間を設定し、Locustによる負荷テストを実行します。
3.  **Docker Composeで起動**: `docker-compose up` を実行し、コンテナ環境でサービスを起動します。

## 📊 API エンドポイント

### ストリーミングチャットエンドポイント

- `POST /chat/stream/with-rag` - RAG機能ありのストリーミングチャット

### リクエスト例

```bash
curl -X POST "http://localhost:8000/chat/stream/with-rag" \
  -H "Content-Type: application/json" \
  -d '{"message": "FastAPIの特徴を説明してください", "user_id": "test_user"}' --no-buffer
```

## 📈 負荷テスト結果の確認

### Locust Web UI

Docker Composeで起動した場合、またはLocustをWeb UIモードで実行した場合、ブラウザで `http://localhost:8089` にアクセスすると、リアルタイムで統計情報を確認できます。

### 主要メトリクス

- **RPS (Requests Per Second)**: 1秒あたりのリクエスト数
- **レスポンス時間**: 平均・95パーセンタイル・99パーセンタイル
- **エラー率**: 失敗したリクエストの割合
- **同時ユーザー数**: アクティブユーザー数

## 🔧 カスタマイズ

### テストメッセージの追加

`locustfile.py`の`test_messages`リストに新しいメッセージを追加することで、テストに使用する質問を増やすことができます。

```python
self.test_messages = [
    "新しいテストメッセージ",
    # 既存のメッセージ...
]
```

## 🐛 トラブルシューティング

### よくある問題

1.  **Azure OpenAI接続エラー**: 環境変数が正しく設定されているか確認し、`python azure_config.py`で接続テストを実行してください。
2.  **メモリ不足**: Dockerのメモリ制限を増やすか、同時ユーザー数を減らしてください。
3.  **レスポンス時間が長い**: Azure OpenAIのクォータ（TPM/RPM）を確認し、必要に応じて上限緩和を申請してください。また、ネットワーク接続も確認してください。

### ログの確認

```bash
# Docker Compose使用時
docker-compose logs -f
```

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。