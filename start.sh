#!/bin/bash

# LangChain FastAPI負荷テストプロジェクト起動スクリプト

set -e

echo "🚀 LangChain FastAPI負荷テストプロジェクトを起動します..."

# 環境変数ファイルの確認
if [ ! -f ".env" ]; then
    echo "⚠️  .envファイルが見つかりません"
    echo "env.exampleをコピーして.envファイルを作成し、Azure OpenAIの設定を行ってください"
    echo "cp env.example .env"
    exit 1
fi

# 依存関係のインストール確認
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成します..."
    python3 -m venv venv
fi

echo "📦 仮想環境をアクティベートします..."
source venv/bin/activate

echo "📦 依存関係をインストールします..."
pip install -r requirements.txt

# Azure OpenAI設定のテスト
echo "🔧 Azure OpenAI設定をテストします..."
python azure_config.py

if [ $? -ne 0 ]; then
    echo "❌ Azure OpenAI設定に問題があります"
    echo "env.exampleファイルを参考に環境変数を設定してください"
    exit 1
fi

echo "✅ Azure OpenAI設定は正常です"

# レポートディレクトリを作成
mkdir -p reports

# 起動方法を選択
echo ""
echo "起動方法を選択してください:"
echo "1) APIサーバーのみ起動"
echo "2) 負荷テストを実行"
echo "3) Docker Composeで起動"
echo "4) 全テストを自動実行"

read -p "選択 (1-4): " choice

case $choice in
    1)
        echo "🚀 APIサーバーを起動します..."
        echo "ブラウザで http://localhost:8000/docs にアクセスしてAPIドキュメントを確認できます"
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 8
        ;;
    2)
        echo "🧪 負荷テストを実行します..."
        read -p "同時ユーザー数: " users
        read -p "生成レート: " spawn_rate
        read -p "実行時間 (例: 5m): " run_time
        python run_load_test.py --users $users --spawn-rate $spawn_rate --run-time $run_time
        ;;
    3)
        echo "🐳 Docker Composeで起動します..."
        docker-compose up -d
        echo "✅ サービスが起動しました"
        echo "APIサーバー: http://localhost:8000"
        echo "Locust Web UI: http://localhost:8089"
        echo "ログ確認: docker-compose logs -f"
        ;;
    4)
        echo "🧪 全テストを自動実行します..."
        python run_load_test.py --test all
        ;;
    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac

