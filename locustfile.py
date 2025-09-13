from locust import HttpUser, task, between, events
import random
import json
import time


class LangChainAPITestUser(HttpUser):
    """LangChain FastAPI負荷テスト用のユーザークラス"""

    wait_time = between(1, 3)  # リクエスト間の待機時間（1-3秒）

    def on_start(self):
        """ユーザーセッション開始時の初期化"""
        self.user_id = f"user_{random.randint(1000, 9999)}"
        self.test_messages = [
            "こんにちは、AIについて教えてください",
            "FastAPIの特徴を説明してください",
            "LangChainとは何ですか？",
            "負荷テストの重要性について教えてください",
            "Azure OpenAIの利点は何ですか？",
            "機械学習と深層学習の違いは何ですか？",
            "自然言語処理の応用例を教えてください",
            "APIの設計で重要なポイントは何ですか？",
            "ストリーミング処理の利点は何ですか？",
            "ベクトルデータベースの用途を教えてください",
        ]

    @task
    def test_stream_chat_with_rag(self):
        """RAG機能ありのストリーミングチャットAPIテスト"""
        message = random.choice(self.test_messages)
        request_name = "stream_chat_with_rag"
        payload = {"message": message, "user_id": self.user_id}
        start_time = time.time()
        try:
            with self.client.post(
                "/chat/stream/with-rag",
                name=request_name,
                json=payload,
                stream=True,
                catch_response=True,
            ) as response:
                response.raise_for_status()
                full_content = ""
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    full_content += chunk

                if not full_content.strip() or "[DONE]" not in full_content:
                    response.failure("Empty or incomplete stream content")
                else:
                    response.success()

        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="POST",
                name=request_name,
                response_time=total_time,
                response_length=0,
                exception=e,
            )


# カスタムイベントハンドラー
from locust import events


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """リクエスト完了時のイベントハンドラー"""
    if exception:
        print(f"リクエスト失敗: {name} - {exception}")
    else:
        print(f"リクエスト成功: {name} - レスポンス時間: {response_time}ms")


@events.user_error.add_listener
def on_user_error(user_instance, exception, tb, **kwargs):
    """ユーザーエラー時のイベントハンドラー"""
    print(f"ユーザーエラー: {exception}")


# テスト設定
class TestConfig:
    """テスト設定クラス"""

    # 基本テスト設定
    BASIC_USERS = 20  # 基本同時ユーザー数
    BASIC_SPAWN_RATE = 2  # ユーザー生成レート（秒）
    BASIC_RUN_TIME = "5m"  # テスト実行時間

    # 高負荷テスト設定
    HIGHLOAD_USERS = 60  # 高負荷同時ユーザー数（50を超える）
    HIGHLOAD_SPAWN_RATE = 5  # ユーザー生成レート（秒）
    HIGHLOAD_RUN_TIME = "10m"  # テスト実行時間

    # 比較テスト設定
    COMPARISON_USERS = 30  # 比較テスト用ユーザー数
    COMPARISON_SPAWN_RATE = 3  # ユーザー生成レート（秒）
    COMPARISON_RUN_TIME = "7m"  # テスト実行時間
