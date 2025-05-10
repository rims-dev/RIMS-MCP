# rims_mcp_client.py
import asyncio
import json

# MCPクライアントのインポート
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from dotenv import load_dotenv
load_dotenv()

async def main():
    # サーバーパラメータの設定
    server_params = StdioServerParameters(command="python", args=["rims_mcp_server.py"])

    # クライアントの初期化と実行
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # セッション初期化
                await session.initialize()
                
                # セッションの属性とメソッドを確認
                print("ClientSession の利用可能なメソッド:")
                session_methods = [method for method in dir(session) if not method.startswith('_') and callable(getattr(session, method))]
                for method in session_methods:
                    print(f"- {method}")
                
                # ツール一覧を取得する方法を試みる
                try:
                    print("\nツール情報の取得を試みます...")
                    
                    # initialize メソッドの結果を使用
                    if hasattr(session, 'tools'):
                        tools = session.tools
                        print(f"セッションから直接ツール情報を取得: {len(tools)} 個のツールが見つかりました")
                    else:
                        # 別の方法でツールにアクセスを試みる
                        print("ツール情報へ直接アクセスできません。list_tools を試みます。")
                        
                        if 'list_tools' in session_methods:
                            # ListToolsResult オブジェクトを取得
                            tools_result = await session.list_tools()
                            
                            # ListToolsResult から実際のツールリストを抽出
                            if hasattr(tools_result, 'tools'):
                                tool_names = tools_result.tools
                                print(f"list_tools メソッドでツールリストを取得: {len(tool_names)} 個のツールが見つかりました")
                            elif hasattr(tools_result, '__dict__'):
                                # __dict__ を使って内部属性にアクセス
                                tool_dict = tools_result.__dict__
                                if 'tools' in tool_dict:
                                    tool_names = tool_dict['tools']
                                    print(f"list_tools メソッドでツールリストを取得: {len(tool_names)} 個のツールが見つかりました")
                                else:
                                    # 辞書の内容を表示して調査
                                    print(f"ツール情報が見つかりません。オブジェクト構造: {tool_dict}")
                                    # フォールバックとして空のリストを使用
                                    tool_names = []
                            else:
                                # オブジェクトの文字列表現を出力して構造を確認
                                print(f"想定外の形式のツール情報です。オブジェクト: {tools_result}")
                                # フォールバックとして空のリストを使用
                                tool_names = []
                            
                            # ツール名をリストとして使用
                            tools = []
                            for tool in tool_names:
                                # 実際のツールオブジェクト構造を調べる
                                if isinstance(tool, str):
                                    # 文字列の場合、ツール名として扱う
                                    tool_info = type('ToolInfo', (), {
                                        'name': tool,
                                        'description': f"Tool: {tool}",
                                        'parameters': {}
                                    })
                                else:
                                    # 文字列でない場合、オブジェクトから情報を抽出
                                    tool_info = type('ToolInfo', (), {
                                        'name': tool.name if hasattr(tool, 'name') else str(tool),
                                        'description': tool.description if hasattr(tool, 'description') else f"Tool: {tool}",
                                        'parameters': tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                                    })
                                tools.append(tool_info)
                        else:
                            # それでもだめならlist_toolsの代わりを見つける
                            print("list_tools メソッドがありません。call_tool を直接使用します。")
                            # ダミーのツールリストを用意
                            tools = []
                    
                    # 利用可能なツールを表示
                    if tools:
                        print("\n利用可能な関数一覧:")
                        for idx, tool in enumerate(tools):
                            # ツール名の表示を整形
                            if isinstance(tool.name, str):
                                tool_name = tool.name
                            else:
                                tool_name = str(tool.name)
                            print(f"{idx+1}. {tool_name}")
                        
                        # ユーザーに選択させる
                        choice = int(input("\n実行する関数番号を選んでください: ")) - 1
                        if choice < 0 or choice >= len(tools):
                            print("無効な選択です。プログラムを終了します。")
                            return
                        
                        selected_tool = tools[choice]
                        print(f"\n選択された関数: {selected_tool.name}")
                        if hasattr(selected_tool, 'description'):
                            print("説明:", selected_tool.description)
                        
                        # 引数情報を取得
                        params = {}
                        if hasattr(selected_tool, 'parameters') and selected_tool.parameters:
                            print("\n引数情報:")
                            print(selected_tool.parameters)
                            
                            # パラメータ処理のためのコード
                            try:
                                # パラメータ情報を取得
                                properties = {}
                                required = []
                                
                                # JSONスキーマ形式の場合
                                if isinstance(selected_tool.parameters, dict):
                                    properties = selected_tool.parameters.get('properties', {})
                                    required = selected_tool.parameters.get('required', [])
                                # オブジェクト形式の場合
                                elif hasattr(selected_tool.parameters, 'properties'):
                                    properties = selected_tool.parameters.properties
                                    if hasattr(selected_tool.parameters, 'required'):
                                        required = selected_tool.parameters.required
                                
                                # パラメータ入力
                                for param_name, param_def in properties.items():
                                    # パラメータの型を取得
                                    param_type = "string"  # デフォルト
                                    if isinstance(param_def, dict):
                                        param_type = param_def.get('type', 'string')
                                    elif hasattr(param_def, 'type'):
                                        param_type = param_def.type
                                    
                                    is_required = param_name in required
                                    req_mark = "*" if is_required else ""
                                    
                                    # ユーザー入力を求める
                                    prompt = f"引数 '{param_name}'{req_mark} を入力してください (型: {param_type}): "
                                    user_input = input(prompt)
                                    
                                    # 空の入力で必須でなければスキップ
                                    if not user_input and not is_required:
                                        continue
                                    
                                    # 型に合わせて変換
                                    try:
                                        if param_type in ['object', 'array']:
                                            value = json.loads(user_input)
                                        elif param_type == 'number':
                                            value = float(user_input)
                                        elif param_type == 'integer':
                                            value = int(user_input)
                                        elif param_type == 'boolean':
                                            value = user_input.lower() in ['true', 'yes', 'y', '1']
                                        else:
                                            value = user_input
                                    except Exception as e:
                                        print(f"警告: パラメータ '{param_name}' の変換に失敗しました: {e}")
                                        value = user_input
                                    
                                    params[param_name] = value
                            
                            except Exception as e:
                                print(f"パラメータ処理中にエラーが発生しました: {e}")
                                print("引数を手動で入力してください...")
                                manual_input = input("引数をJSON形式で入力 (例: {\"key\": \"value\"}): ")
                                if manual_input:
                                    try:
                                        params = json.loads(manual_input)
                                    except json.JSONDecodeError:
                                        print("JSONの解析に失敗しました。空のパラメータで実行します。")
                                        params = {}
                        
                        # 関数実行
                        print(f"\n{selected_tool.name} を実行中...")
                        try:
                            # 実際のツール名を使用するように修正
                            tool_name = selected_tool.name
                            # 念のため文字列型に変換
                            if not isinstance(tool_name, str):
                                print(f"警告: ツール名が文字列型ではありません。型: {type(tool_name)}")
                                tool_name = str(tool_name)
                            
                            result = await session.call_tool(tool_name, params)

                            # result.content から \n をすべて削除して出力
                            content = result.content
                            def remove_newlines(obj):
                                if isinstance(obj, str):
                                    return obj.replace("\n", "")
                                elif isinstance(obj, list):
                                    return [remove_newlines(item) for item in obj]
                                elif isinstance(obj, dict):
                                    return {k: remove_newlines(v) for k, v in obj.items()}
                                else:
                                    return obj

                            cleaned_content = remove_newlines(content)
                            print("\n実行結果 (content):")
                            print(cleaned_content[0].text)

                        except Exception as e:
                            print(f"関数実行中にエラーが発生しました: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print("利用可能なツールがありません。")
                
                except Exception as e:
                    print(f"ツール情報取得中のエラー: {e}")
                    # エラーの詳細情報表示
                    import traceback
                    traceback.print_exc()
    
    except Exception as e:
        print(f"クライアント初期化中のエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())