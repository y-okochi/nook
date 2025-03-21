#!/bin/bash

# 各Lambda関数を即時発火するスクリプト
# 使用方法: ./invoke_lambdas.sh

# エラーが発生したら停止
set -e

echo "Lambda関数を呼び出しています..."

# 実際のLambda関数名（aws lambda list-functions コマンドで確認）
FUNCTIONS=(
  "NookStack-y2okochihackernews0A510DD7-bhaX7zIN01af"
  "NookStack-y2okochipapersummarizer1596DBEE-X0wEpb172NvH"
  "NookStack-y2okochiredditexplorer03F9845C-dgT4URSrLl8i"
  "NookStack-y2okochitechfeedEA11D0A6-htzG81UD9YdS"
  "NookStack-y2okochigithubtrendingCC8AC07F-3iq4koLhNZVA"
)

# 各Lambda関数を呼び出す
for func in "${FUNCTIONS[@]}"; do
  echo "呼び出し中: $func"
  
  # 出力ファイルのパス
  OUTFILE="/tmp/${func}-response.json"
  
  # Lambda関数を呼び出す（EventBridgeイベントを模倣するペイロード）
  aws lambda invoke \
    --function-name "$func" \
    --payload '{"source": "aws.events"}' \
    "$OUTFILE"
  
  # 実行結果を表示
  echo "$func の実行結果:"
  if [ -f "$OUTFILE" ]; then
    cat "$OUTFILE"
  else
    echo "出力ファイルが見つかりません"
  fi
  echo -e "\n"
  
  # 少し待機して、同時に多くのリクエストを送信しないようにする
  sleep 2
done

echo "viewer関数（NookStack-y2okochiviewerFF2BC276-N2PwoQfNeBHy）は情報表示用なので、必要に応じて手動で呼び出してください"
echo "すべてのLambda関数の呼び出しが完了しました"