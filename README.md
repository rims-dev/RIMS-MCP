# RIMS MCP

以下の手順でDockerイメージをビルドしてコンテナを実行できます。

`{your project directory}`を`docker-compose.yml`、`Dockerfile`、`.env`、`rims_mcp_server.py`があるディレクトリに置き換えてください。（`/Users/username/`などのフルパスを指定してください）

## example

Q : ルールの概要を教えて

A : 今年の競技課題は「Asia Traveler」です。この競技では、ロボットが「苗」を回収し、指定されたゾーンに配置した後、国境を越えて別のゾーンに移動し、リングを回収してポールに配置するという一連のタスクを3分以内に行います。競技は赤チームと青チームの対戦形式で行われ、各チームは戦略を駆使して勝利を目指します。  
詳細なルールや競技の進行については、公式ルールブック（最新版はこちら）をご参照ください。

## 🔨 Setup

### `.env`の設定

以下のように`.env`ファイルを作成してください。  
WEB_PAGE_URLの末尾には`/`を忘れずに追加してください。

```env
API_ENDPOINT=https://rims.tourobo.net
WEB_PAGE_URL=https://tourobo.net/
COMPETITION_ID=nNzAy
```

### ⚙️ VSCode Copilot / Claude Desktopの設定

#### VSCode Copilot (setting.json)

```json
{
  "mcp": {
    "servers": {
      "rims-mcp": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e", "API_ENDPOINT=https://rims.tourobo.net",
          "-e", "WEB_PAGE_URL=https://tourobo.net/",
          "-e", "COMPETITION_ID=nNzAy",
          "xyzme01/rims-mcp"
        ],
        "alwaysAllow": [
          "get_faq",
          "get_rules",
          "get_faq_keyword"
        ]
      }
    }
  }
}
```

#### Claude Desktop (claude_desktop_config.json)

```json
{
    "mcpServers": {
        "rims-mcp": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e", "API_ENDPOINT=https://rims.tourobo.net",
                "-e", "WEB_PAGE_URL=https://tourobo.net/",
                "-e", "COMPETITION_ID=nNzAy",
                "xyzme01/rims-mcp"
            ],
            "alwaysAllow": [
                "get_faq",
                "get_rules",
                "get_faq_keyword"
            ]
        }
    }
}
```

## Dockerへのビルド方法

```bash
# Dockerイメージのビルド
docker build -t xyzme01/rims-mcp:latest .

# Docker Hubへのプッシュ
docker push xyzme01/rims-mcp:latest
```

## ローカルでの実行方法

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python rims_mcp_client.py
```
