#!/bin/bash

# EventBridgeルールを即時トリガーするスクリプト
# 使用方法: ./trigger_eventbridge_rules.sh

# エラーが発生したら停止
set -e

echo "EventBridgeルールを即時トリガーしています..."

# EventBridgeルールのリスト
RULES=(
  "NookStack-y2okochiDaily2030Rule0526B9ADA-uUUy2fngeZYZ"  # hacker_news
  "NookStack-y2okochiDaily2030Rule16DAAC7F7-UcKwMTMm7EkP"  # paper_summarizer
  "NookStack-y2okochiDaily2030Rule2B240075C-3Ke3AYUcrAvi"  # reddit_explorer
  "NookStack-y2okochiDaily2030Rule3EAA0FA7D-LVr6voPNYmJI"  # tech_feed
  "NookStack-y2okochiDaily2030Rule45EA0C1F1-CreUQ8ybYl55"  # github_trending
)

# 現在時刻の1分後を計算（cron式用）
CURRENT_MINUTE=$(date -u -d "+1 minute" +%M)
CURRENT_HOUR=$(date -u -d "+1 minute" +%H)
CURRENT_DAY=$(date -u -d "+1 minute" +%d)
CURRENT_MONTH=$(date -u -d "+1 minute" +%m)
CURRENT_YEAR=$(date -u -d "+1 minute" +%Y)

# 各ルールの元のスケジュールを保存
declare -A ORIGINAL_SCHEDULES

# 各ルールのスケジュールを変更して即時実行
for rule in "${RULES[@]}"; do
  echo "ルール $rule の元のスケジュールを保存しています..."
  
  # 元のスケジュールを取得して保存
  ORIGINAL_SCHEDULE=$(aws events describe-rule --name "$rule" --query "ScheduleExpression" --output text)
  ORIGINAL_SCHEDULES["$rule"]="$ORIGINAL_SCHEDULE"
  
  echo "ルール $rule のスケジュールを変更しています..."
  
  # スケジュールを現在時刻の1分後に変更
  NEW_SCHEDULE="cron($CURRENT_MINUTE $CURRENT_HOUR $CURRENT_DAY $CURRENT_MONTH ? $CURRENT_YEAR)"
  aws events put-rule --name "$rule" --schedule-expression "$NEW_SCHEDULE"
  
  echo "ルール $rule のスケジュールを $NEW_SCHEDULE に変更しました"
done

echo "すべてのルールのスケジュールを変更しました。1分以内に実行されます..."
echo "60秒待機しています..."
sleep 60

echo "ルールが実行されました。元のスケジュールに戻しています..."

# 各ルールのスケジュールを元に戻す
for rule in "${RULES[@]}"; do
  echo "ルール $rule のスケジュールを元に戻しています..."
  
  # スケジュールを元に戻す
  aws events put-rule --name "$rule" --schedule-expression "${ORIGINAL_SCHEDULES["$rule"]}"
  
  echo "ルール $rule のスケジュールを ${ORIGINAL_SCHEDULES["$rule"]} に戻しました"
done

echo "すべてのルールのスケジュールを元に戻しました"
echo "EventBridgeルールのトリガーが完了しました"