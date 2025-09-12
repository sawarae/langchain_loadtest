"""
Azure OpenAI設定とヘルパー関数
"""
import os
from typing import Optional
import logging
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class AzureOpenAIConfig:
    """Azure OpenAI設定クラス"""
    
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.embedding_deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    
    def validate_config(self) -> bool:
        """設定の妥当性を検証"""
        required_fields = [
            self.api_key,
            self.endpoint,
            self.deployment_name,
            self.embedding_deployment_name
        ]
        
        if not all(required_fields):
            missing_fields = []
            if not self.api_key:
                missing_fields.append("AZURE_OPENAI_API_KEY")
            if not self.endpoint:
                missing_fields.append("AZURE_OPENAI_ENDPOINT")
            if not self.deployment_name:
                missing_fields.append("AZURE_OPENAI_DEPLOYMENT_NAME")
            if not self.embedding_deployment_name:
                missing_fields.append("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
            
            logger.error(f"必要な環境変数が設定されていません: {', '.join(missing_fields)}")
            return False
        
        # エンドポイントの形式をチェック
        if not self.endpoint.startswith("https://") or not self.endpoint.endswith("/"):
            logger.error("AZURE_OPENAI_ENDPOINTは 'https://your-resource.openai.azure.com/' の形式である必要があります")
            return False
        
        logger.info("Azure OpenAI設定が正常に検証されました")
        return True
    
    def get_config_dict(self) -> dict:
        """設定を辞書形式で取得"""
        return {
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "api_version": self.api_version,
            "deployment_name": self.deployment_name,
            "embedding_deployment_name": self.embedding_deployment_name
        }

def setup_azure_openai():
    """Azure OpenAIの設定と初期化"""
    config = AzureOpenAIConfig()
    
    if not config.validate_config():
        raise ValueError("Azure OpenAI設定が無効です。環境変数を確認してください。")
    
    return config

def test_azure_connection():
    """Azure OpenAI接続テスト"""
    try:
        from langchain_openai import AzureChatOpenAI
        from langchain_community.embeddings import AzureOpenAIEmbeddings
        
        config = setup_azure_openai()
        
        # チャットモデルのテスト
        llm = AzureChatOpenAI(
            azure_deployment=config.deployment_name,
            openai_api_version=config.api_version,
            openai_api_key=config.api_key,
            azure_endpoint=config.endpoint,
            temperature=0.1,
            max_completion_tokens=10
        )
        
        # 埋め込みモデルのテスト
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=config.embedding_deployment_name,
            openai_api_version=config.api_version,
            openai_api_key=config.api_key,
            azure_endpoint=config.endpoint
        )
        
        logger.info("Azure OpenAI接続テストが成功しました")
        return True
        
    except Exception as e:
        logger.error(f"Azure OpenAI接続テストが失敗しました: {e}")
        return False

if __name__ == "__main__":
    # 設定テスト
    logging.basicConfig(level=logging.INFO)
    
    print("Azure OpenAI設定テストを開始します...")
    
    if test_azure_connection():
        print("✅ Azure OpenAI設定は正常です")
    else:
        print("❌ Azure OpenAI設定に問題があります")
        print("env.exampleファイルを参考に環境変数を設定してください")
