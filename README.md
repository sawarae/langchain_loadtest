# LangChain FastAPI 負荷テストプロジェクト by cursor agent

このプロジェクトは、LangChainとFastAPIで構築されたAPIの負荷テストをLocustで実行し、同時並列数50を超えられるか検証するためのものです。RAG機能ありとなしでの性能比較も含まれています。

## 🚀 機能

- **FastAPI + LangChain API**: RAG機能ありとなしの両方のエンドポイント
- **Azure OpenAI統合**: GPT-4と埋め込みモデルの利用
- **Locust負荷テスト**: 同時並列数50を超える検証
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

### 方法1: 直接実行

#### APIサーバーの起動

```bash
python main.py
```

または

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 負荷テストの実行

```bash
# 基本負荷テスト（同時ユーザー数20）
locust -f locustfile.py --host=http://localhost:8000 --users=20 --spawn-rate=2 --run-time=5m

# 高負荷テスト（同時ユーザー数60、50を超える検証）
locust -f locustfile.py --host=http://localhost:8000 --users=60 --spawn-rate=1 --run-time=10m

# Web UIでの実行
locust -f locustfile.py --host=http://localhost:8000 --web-host=0.0.0.0
```

### 方法2: Docker Compose

```bash
# 環境変数を設定
export AZURE_OPENAI_API_KEY="your_key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="your-embedding-deployment"

# サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f langchain-api
```

## 📊 API エンドポイント

### 基本エンドポイント

- `GET /` - ヘルスチェック
- `GET /health` - 詳細ヘルスチェック

### チャットエンドポイント

- `POST /chat/without-rag` - RAG機能なしのチャット
- `POST /chat/with-rag` - RAG機能ありのチャット
- `GET /chat/stream/without-rag` - RAG機能なしのストリーミングチャット
- `GET /chat/stream/with-rag` - RAG機能ありのストリーミングチャット

### リクエスト例

```bash
# RAG機能なし
curl -X POST "http://localhost:8000/chat/without-rag" \
  -H "Content-Type: application/json" \
  -d '{"message": "AIについて教えてください", "user_id": "test_user"}'

# RAG機能あり
curl -X POST "http://localhost:8000/chat/with-rag" \
  -H "Content-Type: application/json" \
  -d '{"message": "FastAPIの特徴を説明してください", "user_id": "test_user"}'
```

## 🧪 負荷テストシナリオ

### 1. 基本負荷テスト
- **同時ユーザー数**: 20
- **生成レート**: 2ユーザー/秒
- **実行時間**: 5分
- **目的**: 基本的な性能確認

### 2. 高負荷テスト（50並列超え検証）
- **同時ユーザー数**: 60
- **生成レート**: 5ユーザー/秒
- **実行時間**: 10分
- **目的**: 同時並列数50を超える検証

### 3. 比較テスト
- **同時ユーザー数**: 30
- **生成レート**: 3ユーザー/秒
- **実行時間**: 7分
- **目的**: RAG機能ありとなしでの性能比較

## 📈 負荷テスト結果の確認

### Locust Web UI
- ブラウザで `http://localhost:8089` にアクセス
- リアルタイムで統計情報を確認

### 主要メトリクス
- **RPS (Requests Per Second)**: 1秒あたりのリクエスト数
- **レスポンス時間**: 平均・95パーセンタイル・99パーセンタイル
- **エラー率**: 失敗したリクエストの割合
- **同時ユーザー数**: アクティブユーザー数

## 🔧 カスタマイズ

### 負荷テストの調整

`locustfile.py`の`TestConfig`クラスで設定を変更できます：

```python
class TestConfig:
    BASIC_USERS = 20
    HIGHLOAD_USERS = 60  # この値を変更
    COMPARISON_USERS = 30
```

### テストメッセージの追加

`locustfile.py`の`test_messages`リストに新しいメッセージを追加：

```python
self.test_messages = [
    "新しいテストメッセージ",
    # 既存のメッセージ...
]
```

## 🐛 トラブルシューティング

### よくある問題

1. **Azure OpenAI接続エラー**
   - 環境変数が正しく設定されているか確認
   - `python azure_config.py`で接続テストを実行

2. **メモリ不足**
   - Dockerのメモリ制限を増やす
   - 同時ユーザー数を減らす

3. **レスポンス時間が長い**
   - Azure OpenAIのクォータを確認
   - ネットワーク接続を確認

### ログの確認

```bash
# Docker Compose使用時
docker-compose logs -f langchain-api

# 直接実行時
tail -f logs/app.log
```

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

## 📞 サポート

問題が発生した場合は、GitHubのIssuesページで報告してください。
