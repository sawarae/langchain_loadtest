from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# 環境変数を読み込み
load_dotenv()
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import logging
import time
import wandb
import weave
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# wandbとWeaveの初期化（オフラインモード）
wandb_initialized = False
weave_initialized = False

try:
    wandb.init(
        project=os.getenv("WANDB_PROJECT", "langchain-load-test"),
        config={
            "azure_openai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "azure_openai_embedding_deployment": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "workers": 4
        }
    )
    wandb_initialized = True
    # logger.info("wandb初期化成功（オフラインモード）")
except Exception as e:
    logger.warning(f"wandb初期化失敗: {e}")

# Weaveの初期化（スキップ）
logger.info("Weave初期化をスキップ（オフラインモード）")

# パフォーマンス測定用のヘルパー関数
def log_performance_metrics(endpoint_name, processing_time, success, error_type=None, user_id=None):
    """パフォーマンスメトリクスをwandbとWeaveに記録"""
    metrics = {
        "endpoint": endpoint_name,
        "processing_time": processing_time,
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id or "unknown"
    }
    
    if error_type:
        metrics["error_type"] = error_type
    
    # wandbに記録
    if wandb_initialized:
        try:
            wandb.log(metrics)
        except Exception as e:
            logger.warning(f"wandb記録失敗: {e}")
    
    # Weaveに記録（スキップ）
    # weave.log(metrics, "performance_metrics")
    
    # ログ出力
    if success:
        logger.info(f"✅ {endpoint_name} - 処理時間: {processing_time:.2f}秒 - ユーザー: {user_id}")
    else:
        logger.error(f"❌ {endpoint_name} - エラー: {error_type} - 処理時間: {processing_time:.2f}秒 - ユーザー: {user_id}")

app = FastAPI(title="LangChain FastAPI Load Test", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure OpenAI設定
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# グローバル変数をNoneで初期化（マルチワーカー対応）
llm = None
embeddings = None
vectorstore = None

def get_llm():
    """LLMインスタンスを取得（遅延初期化）"""
    global llm
    if llm is None:
        llm = AzureChatOpenAI(
            azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
            openai_api_version=AZURE_OPENAI_API_VERSION,
            openai_api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            temperature=1.0,
            model_kwargs={
                "max_completion_tokens": 1000
            }
        )
    return llm

def get_embeddings():
    """Embeddingsインスタンスを取得（遅延初期化）"""
    global embeddings
    if embeddings is None:
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
            openai_api_version=AZURE_OPENAI_API_VERSION,
            openai_api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )
    return embeddings

def get_vectorstore():
    """ベクトルストアインスタンスを取得（遅延初期化）"""
    global vectorstore
    if vectorstore is None:
        try:
            # テキスト分割器
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            
            # ドキュメントを分割
            documents = text_splitter.create_documents(SAMPLE_DOCUMENTS)
            
            # FAISSベクトルストアを作成
            vectorstore = FAISS.from_documents(documents, get_embeddings())
            logger.info("ベクトルストアが正常に初期化されました")
        except Exception as e:
            logger.error(f"ベクトルストアの初期化に失敗しました: {e}")
            vectorstore = None
    return vectorstore

# リクエストモデル
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"

class ChatResponse(BaseModel):
    response: str
    user_id: str
    timestamp: str
    processing_time: float

# サンプルドキュメント（RAG用）
SAMPLE_DOCUMENTS = [
    "人工知能（AI）は、コンピュータが人間の知能を模倣する技術です。機械学習、深層学習、自然言語処理などの分野が含まれます。",
    "FastAPIは、PythonのWebフレームワークで、高いパフォーマンスと自動的なAPIドキュメント生成が特徴です。",
    "LangChainは、大規模言語モデル（LLM）を活用したアプリケーション開発を支援するフレームワークです。",
    "負荷テストは、システムの性能を測定し、同時接続数やレスポンス時間を評価するためのテスト手法です。",
    "Azure OpenAIは、Microsoft Azure上で提供されるOpenAIのサービスで、GPT-4やGPT-3.5などのモデルを利用できます。"
]


@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {"message": "LangChain FastAPI Load Test API", "status": "healthy"}

@app.get("/health")
async def health_check():
    """詳細なヘルスチェック"""
    try:
        # 各コンポーネントの初期化をテスト
        get_llm()
        get_embeddings()
        get_vectorstore()
        
        return {
            "status": "healthy",
            "vectorstore_initialized": get_vectorstore() is not None,
            "azure_openai_configured": all([
                AZURE_OPENAI_API_KEY,
                AZURE_OPENAI_ENDPOINT,
                AZURE_OPENAI_DEPLOYMENT_NAME
            ]),
            "workers": "multi-worker mode"
        }
    except Exception as e:
        logger.error(f"ヘルスチェックでエラー: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@weave.op()
async def astream_chat_without_rag(message: str, user_id: str) -> AsyncGenerator[str, None]:
    """RAG機能なしのチャット（ストリーミング）"""
    try:
        llm_instance = get_llm()
        messages = [
            SystemMessage(content="あなたは親切で知識豊富なAIアシスタントです。日本語で回答してください。"),
            HumanMessage(content=message)
        ]
        
        async for chunk in llm_instance.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"RAGなしチャットでエラーが発生しました: {e}")
        
        # レート制限エラーの詳細記録
        if "429" in error_msg or "rate limit" in error_msg.lower():
            log_performance_metrics("azure_openai_rate_limit", 0, False, "rate_limit_error", user_id)
        
        yield f"エラーが発生しました: {error_msg}"

@weave.op()
async def astream_chat_with_rag(message: str, user_id: str) -> AsyncGenerator[str, None]:
    """RAG機能ありのチャット（ストリーミング）"""
    try:
        vectorstore_instance = get_vectorstore()
        if vectorstore_instance is None:
            yield "ベクトルストアが初期化されていません。RAG機能を利用できません。"
            return
            
        # 関連ドキュメントを検索
        relevant_docs = vectorstore_instance.similarity_search(message, k=3)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        system_prompt = f"""あなたは親切で知識豊富なAIアシスタントです。以下のコンテキスト情報を参考にして、日本語で回答してください。

コンテキスト情報:
{context}

質問に答える際は、上記のコンテキスト情報を活用してください。"""
        
        llm_instance = get_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        async for chunk in llm_instance.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"RAGありチャットでエラーが発生しました: {e}")
        
        # レート制限エラーの詳細記録
        if "429" in error_msg or "rate limit" in error_msg.lower():
            log_performance_metrics("azure_openai_rate_limit", 0, False, "rate_limit_error", user_id)
        
        yield f"エラーが発生しました: {error_msg}"

@app.post("/chat/without-rag", response_model=ChatResponse)
async def chat_without_rag(request: ChatRequest):
    """RAG機能なしのチャットエンドポイント"""
    start_time = time.time()
    
    try:
        response_text = ""
        async for chunk in astream_chat_without_rag(request.message, request.user_id):
            response_text += chunk
        
        processing_time = time.time() - start_time
        
        # パフォーマンスメトリクスを記録
        log_performance_metrics("chat_without_rag", processing_time, True, user_id=request.user_id)
        
        return ChatResponse(
            response=response_text,
            user_id=request.user_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_type = type(e).__name__
        
        # エラーメトリクスを記録
        log_performance_metrics("chat_without_rag", processing_time, False, error_type, request.user_id)
        
        logger.error(f"RAGなしチャットエンドポイントでエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/with-rag", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest):
    """RAG機能ありのチャットエンドポイント"""
    start_time = time.time()
    
    try:
        response_text = ""
        async for chunk in astream_chat_with_rag(request.message, request.user_id):
            response_text += chunk
        
        processing_time = time.time() - start_time
        
        # パフォーマンスメトリクスを記録
        log_performance_metrics("chat_with_rag", processing_time, True, user_id=request.user_id)
        
        return ChatResponse(
            response=response_text,
            user_id=request.user_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_type = type(e).__name__
        
        # エラーメトリクスを記録
        log_performance_metrics("chat_with_rag", processing_time, False, error_type, request.user_id)
        
        logger.error(f"RAGありチャットエンドポイントでエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/stream/without-rag")
async def stream_chat_without_rag(message: str, user_id: str = "default_user"):
    """RAG機能なしのストリーミングチャットエンドポイント"""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate():
        async for chunk in astream_chat_without_rag(message, user_id):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/chat/stream/with-rag")
async def stream_chat_with_rag(message: str, user_id: str = "default_user"):
    """RAG機能ありのストリーミングチャットエンドポイント"""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate():
        async for chunk in astream_chat_with_rag(message, user_id):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
