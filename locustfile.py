from locust import HttpUser, task, between
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
            "ベクトルデータベースの用途を教えてください"
        ]
    
    @task(3)
    def test_chat_without_rag(self):
        """RAG機能なしのチャットAPIテスト（重み3）"""
        message = random.choice(self.test_messages)
        
        payload = {
            "message": message,
            "user_id": self.user_id
        }
        
        with self.client.post(
            "/chat/without-rag",
            json=payload,
            catch_response=True,
            name="chat_without_rag"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("response") and len(data["response"]) > 0:
                        response.success()
                        # レスポンス時間をログに記録
                        processing_time = data.get("processing_time", 0)
                        if processing_time > 15.0:  # 5秒以上かかった場合
                            response.failure(f"処理時間が長すぎます: {processing_time}秒")
                    else:
                        response.failure("空のレスポンス")
                except json.JSONDecodeError:
                    response.failure("無効なJSONレスポンス")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")
    
    @task(3)
    def test_chat_with_rag(self):
        """RAG機能ありのチャットAPIテスト（重み3）"""
        message = random.choice(self.test_messages)
        
        payload = {
            "message": message,
            "user_id": self.user_id
        }
        
        with self.client.post(
            "/chat/with-rag",
            json=payload,
            catch_response=True,
            name="chat_with_rag"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("response") and len(data["response"]) > 0:
                        response.success()
                        # レスポンス時間をログに記録
                        processing_time = data.get("processing_time", 0)
                        if processing_time > 15.0:  # RAGは処理時間が長いため8秒
                            response.failure(f"処理時間が長すぎます: {processing_time}秒")
                    else:
                        response.failure("空のレスポンス")
                except json.JSONDecodeError:
                    response.failure("無効なJSONレスポンス")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")
    
    @task(1)
    def test_stream_chat_without_rag(self):
        """RAG機能なしのストリーミングチャットAPIテスト（重み1）"""
        message = random.choice(self.test_messages)
        
        with self.client.get(
            f"/chat/stream/without-rag?message={message}&user_id={self.user_id}",
            catch_response=True,
            name="stream_chat_without_rag",
            stream=True
        ) as response:
            if response.status_code == 200:
                content_received = False
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk and chunk.strip():
                        content_received = True
                        break
                
                if content_received:
                    response.success()
                else:
                    response.failure("ストリーミングコンテンツが受信されませんでした")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")
    
    @task(1)
    def test_stream_chat_with_rag(self):
        """RAG機能ありのストリーミングチャットAPIテスト（重み1）"""
        message = random.choice(self.test_messages)
        
        with self.client.get(
            f"/chat/stream/with-rag?message={message}&user_id={self.user_id}",
            catch_response=True,
            name="stream_chat_with_rag",
            stream=True
        ) as response:
            if response.status_code == 200:
                content_received = False
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk and chunk.strip():
                        content_received = True
                        break
                
                if content_received:
                    response.success()
                else:
                    response.failure("ストリーミングコンテンツが受信されませんでした")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")
    
    @task(1)
    def test_health_check(self):
        """ヘルスチェックAPIテスト（重み1）"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="health_check"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure(f"ヘルスチェック失敗: {data}")
                except json.JSONDecodeError:
                    response.failure("無効なJSONレスポンス")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")

class HighLoadTestUser(HttpUser):
    """高負荷テスト用のユーザークラス（同時並列数50を超える検証）"""
    
    wait_time = between(0.5, 1.5)  # より短い待機時間
    
    def on_start(self):
        """ユーザーセッション開始時の初期化"""
        self.user_id = f"highload_user_{random.randint(10000, 99999)}"
        self.quick_messages = [
            "AIとは？",
            "FastAPIとは？",
            "LangChainとは？",
            "負荷テストとは？",
            "Azure OpenAIとは？"
        ]
    
    @task(5)
    def test_quick_chat_without_rag(self):
        """RAG機能なしのクイックチャットテスト（重み5）"""
        message = random.choice(self.quick_messages)
        
        payload = {
            "message": message,
            "user_id": self.user_id
        }
        
        with self.client.post(
            "/chat/without-rag",
            json=payload,
            catch_response=True,
            name="quick_chat_without_rag"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("response"):
                        response.success()
                    else:
                        response.failure("空のレスポンス")
                except json.JSONDecodeError:
                    response.failure("無効なJSONレスポンス")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)
    def test_quick_chat_with_rag(self):
        """RAG機能ありのクイックチャットテスト（重み3）"""
        message = random.choice(self.quick_messages)
        
        payload = {
            "message": message,
            "user_id": self.user_id
        }
        
        with self.client.post(
            "/chat/with-rag",
            json=payload,
            catch_response=True,
            name="quick_chat_with_rag"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("response"):
                        response.success()
                    else:
                        response.failure("空のレスポンス")
                except json.JSONDecodeError:
                    response.failure("無効なJSONレスポンス")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def test_health_check(self):
        """ヘルスチェックAPIテスト（重み2）"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="health_check_highload"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

# カスタムイベントハンドラー
from locust import events

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
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
