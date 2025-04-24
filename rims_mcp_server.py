from mcp.server.fastmcp import FastMCP
import dotenv
import os
import aiohttp
import tempfile
from pytesseract import image_to_string
from PIL import Image
import io
from pdfminer.high_level import extract_text

# .envファイルから環境変数を読み込む
dotenv.load_dotenv()

# APIのエンドポイント / 大会IDを.envファイルから取得
API_ENDPOINT = os.getenv("API_ENDPOINT", "").strip()
COMPETITION_ID = os.getenv("COMPETITION_ID", "").strip()
WEB_PAGE_URL = os.getenv("WEB_PAGE_URL", "").strip()

# 環境変数が取得できていない場合のエラーハンドリング
if not API_ENDPOINT:
    raise ValueError("API_ENDPOINT is not set in the .env file.")
if not COMPETITION_ID:
    raise ValueError("COMPETITION_ID is not set in the .env file.")
if not WEB_PAGE_URL:
    raise ValueError("WEB_PAGE_URL is not set in the .env file.")

# FastMCPを使用してサーバを作成
mcp = FastMCP(title="RIMS-MCP", description="RIMSのMCPサーバ", api_endpoint=API_ENDPOINT, competition_id=COMPETITION_ID)

# MCPツールとしてget_faqを定義
@mcp.tool()
async def get_faq():
    """
    FAQを取得するツール（全件）
    """
    url = f"{API_ENDPOINT}/api/v2/web/competition/get_faq.php?id={COMPETITION_ID}&query="
    headers = {"Referer": WEB_PAGE_URL}  # "Referer" is the correct HTTP header name
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # FAQデータを整形して返す
                return {
                    "faq": [
                        {
                            "number": item.get("number"),
                            "question": item.get("question", ""),
                            "answer": item.get("answer", ""),
                            "question_image": item.get("question_image"),
                            "answer_image": item.get("answer_image"),
                        }
                        for item in data.get("answered", [])
                    ]
                }
            else:
                return {"error": f"Failed to fetch FAQ. Status code: {response.status}"}



@mcp.tool()
async def get_faq_keyword(keyword: str):
    """
    FAQを取得するツール（キーワード検索）
    """
    url = f"{API_ENDPOINT}/api/v2/web/competition/get_faq.php?id={COMPETITION_ID}&query={keyword}"
    headers = {"Referer": WEB_PAGE_URL}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # FAQデータを整形して返す
                return {
                    "faq": [
                        {
                            "number": item.get("number"),
                            "question": item.get("question", ""),
                            "answer": item.get("answer", ""),
                            "question_image": item.get("question_image"),
                            "answer_image": item.get("answer_image"),
                        }
                        for item in data.get("answered", [])
                    ]
                }
            else:
                return {"error": f"Failed to fetch FAQ. Status code: {response.status}"}


@mcp.tool()
async def get_rules():
    """
    ルールブックの最新版を取得するツール
    """
    # リファラを偽装してAPIからルールブックを取得する処理を実装(WEB_PAGE_URLにリファラを指定)
    # /api/v2/web/competition/get_rule.php?id={COMPETITION_ID}
    url = f"{API_ENDPOINT}/api/v2/web/competition/get_rule.php?id={COMPETITION_ID}"
    headers = {"Referer": WEB_PAGE_URL}  # "Referer" is the correct HTTP header name

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()

                # 最新のルールブックのみを取得
                latest_rule_book = max(
                    data.get("rules", {}).get("rule_books", []),
                    key=lambda x: x.get("date", ""),
                    default=None
                )

                # latest_rule_bookのURLを取得
                if latest_rule_book:
                    latest_rule_book_url = latest_rule_book.get("url", "")
                else:
                    latest_rule_book_url = None

                if latest_rule_book_url:
                    # PDFのURLを受け取り、OCRを実行してテキストを返すツール
                    ocr_text = await pdf_ocr(latest_rule_book_url)
                else:
                    ocr_text = "No rule book available."

                rules = {
                    "name": data.get("rules", {}).get("name", "No name provided."),
                    "abstract": data.get("rules", {}).get("abstract", "No abstract provided."),
                    "rule": ocr_text,
                    "latest_rule_book": latest_rule_book,
                    "field_books": data.get("rules", {}).get("field_books", []),
                    "other_documents": data.get("rules", {}).get("other_documents", [])
                }

                return {"rules": rules}
            else:
                return {"error": f"Failed to fetch rules. Status code: {response.status}"}


import aiohttp
import tempfile
import os
from typing import Union
from pdfminer.high_level import extract_text  # または別のOCRライブラリ
# WEB_PAGE_URL はグローバル定義済みと仮定

async def pdf_ocr(url: str) -> Union[str, dict]:
    """
    PDFのURLを受け取り、OCRを実行してテキストを返すツール
    """
    headers = {"Referer": WEB_PAGE_URL}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return {"error": f"Failed to fetch PDF. Status code: {response.status}"}

                data = await response.read()

    except aiohttp.ClientError as e:
        return {"error": f"HTTP request failed: {str(e)}"}

    # 一時ファイルへの保存とOCR処理
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(data)
            temp_file_path = temp_file.name

        try:
            ocr_text = extract_text(temp_file_path)
        except Exception as e:
            return {"error": f"PDF text extraction failed: {str(e)}"}
        finally:
            os.unlink(temp_file_path)

        return ocr_text

    except Exception as e:
        return {"error": f"Temporary file operation failed: {str(e)}"}

if __name__ == "__main__":
    # json-rpc ではなく stdio を使用する
    mcp.run(transport="stdio")