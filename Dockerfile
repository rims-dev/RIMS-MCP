# Use the official Python 3.12 image as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . /app

# 環境変数が設定されていることを確認するためのスクリプト
RUN echo '#!/bin/bash\necho "API_ENDPOINT: $API_ENDPOINT"\necho "WEB_PAGE_URL: $WEB_PAGE_URL"\necho "COMPETITION_ID: $COMPETITION_ID"\necho "環境変数チェック完了"\nexec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# entrypoint スクリプトを設定
ENTRYPOINT ["/entrypoint.sh"]

# デフォルトではコンテナが終了しないようにする
CMD ["tail", "-f", "/dev/null"]