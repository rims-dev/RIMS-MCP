# rims_mcp_server.py
from mcp.server.fastmcp import FastMCP
import os
import aiohttp
import tempfile
from PIL import Image
from typing import Union
from pdfminer.high_level import extract_text

from dotenv import load_dotenv
load_dotenv(override=False, verbose=False)

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

@mcp.tool()
async def get_news_list():
    """
    ニュース一覧を取得するツール(/api/v2/web/competition/get_news.php?id={COMPETITION_ID})
    """
    url = f"{API_ENDPOINT}/api/v2/web/competition/get_news.php?id={COMPETITION_ID}"
    headers = {"Referer": WEB_PAGE_URL}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {"news": data.get("news", [])}
            else:
                return {"error": f"Failed to fetch news. Status code: {response.status}"}

@mcp.tool()
async def get_news_article(article_id: str):
    """
    ニュース記事を取得するツール(/api/v2/web/competition/get_article.php?id={COMPETITION_ID}&article_id={article_id})
    """
    url = f"{API_ENDPOINT}/api/v2/web/competition/get_article.php?id={COMPETITION_ID}&article_id={article_id}"
    headers = {"Referer": WEB_PAGE_URL}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # PDF URLが存在する場合はOCRも実行
                pdf_url = data.get("pdf_url")
                ocr_text = None
                if pdf_url:
                    ocr_text = await pdf_ocr(pdf_url)
                return {
                    "news": {
                        "title": data.get("article_title", data.get("title", "")),
                        "content": data.get("article", data.get("content", "")),
                        "date": data.get("date", ""),
                        "image": data.get("image", ""),
                        "pdf_url": pdf_url,
                        "ocr_text": ocr_text
                    }
                }
            else:
                return {"error": f"Failed to fetch news article. Status code: {response.status}"}

@mcp.tool()
async def get_team_list():
    """
    チーム一覧を取得するツール(/api/v2/web/competition/get_team.php?id={COMPETITION_ID})
    チーム状態(status)は以下の通り:
        0: 状態非公開
        1: エントリー済み
        2: 書類審査通過
        3: ビデオ審査通過
        4: 大会出場
        5: 出場辞退
        6: 出場取り消し
        7: 出場取りやめ
        8: 書類審査落選
        9: ビデオ審査落選
        10: 審査中
        11: エキシビジョン参加
        12: 不明
    """
    TEAM_STATUS_MAP = {
        0: "状態非公開",
        1: "エントリー済み",
        2: "書類審査通過",
        3: "ビデオ審査通過",
        4: "大会出場",
        5: "出場辞退",
        6: "出場取り消し",
        7: "出場取りやめ",
        8: "書類審査落選",
        9: "ビデオ審査落選",
        10: "審査中",
        11: "エキシビジョン参加",
        12: "不明"
    }
    url = f"{API_ENDPOINT}/api/v2/web/competition/get_teams.php?id={COMPETITION_ID}"
    headers = {"Referer": WEB_PAGE_URL}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                teams = []
                for team in data.get("teams", []):
                    status_code = team.get("status")
                    status_label = TEAM_STATUS_MAP.get(status_code, "不明")
                    teams.append({
                        "team_name": team.get("team_name", ""),
                        "team_org": team.get("team_org", ""),
                        "team_icon": team.get("team_icon"),
                        "team_homepage": team.get("team_homepage"),
                        "team_twitter": team.get("team_twitter"),
                        "team_facebook": team.get("team_facebook"),
                        "team_instagram": team.get("team_instagram"),
                        "team_tiktok": team.get("team_tiktok"),
                        "team_bluesky": team.get("team_bluesky"),
                        "status_label": status_label,
                        "data": team.get("data"),
                        "match": team.get("match"),
                    })
                return {"teams": teams}
            else:
                return {"error": f"Failed to fetch team list. Status code: {response.status}"}



# PDFのURLを受け取り、OCRを実行してテキストを返すツール
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