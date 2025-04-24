import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

async def main():
    # mini_server.py をPythonで実行し、stdin/stdoutで接続
    server_params = StdioServerParameters(command="python", args=["rims_mcp_server.py"])

    # サーバ接続のためのクライアントストリームを確立
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 初期化処理（initialize）
            await session.initialize()

            # "hello_world" ツールを呼び出し
            # result = await session.call_tool("get_rules", {"name": "MCP"})
            result = await session.call_tool("get_rules", {})
            # result = await session.call_tool("pdf_ocr", {"url": "https://rims.tourobo.net/document/?doc=docu_JeR0fJv9NavJGgepuQfg"})
            print("Tool result:", result.content)

if __name__ == "__main__":
    asyncio.run(main())
