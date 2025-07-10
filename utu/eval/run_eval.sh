#!/bin/bash
export SERPER_API_KEY="1b2e7633dc16990218f7097ff434f65d75141fe6"
export JINA_API_KEY="jina_77be9eda14bc413f85f7b18d482ffa1elxJ2dJRs_71v4l_NNS1AJYSm47kM"


# 设置最大重试次数（可选，设置为0表示无限重试）
MAX_RETRIES=0
# 设置重试间隔时间（秒）
RETRY_DELAY=5

COMMAND="python utu/eval/run_eval.py"

# 计数器
retry_count=0

while true; do
    # 执行命令
    $COMMAND
    
    # 检查退出状态
    exit_status=$?
    if [ $exit_status -eq 0 ]; then
        echo "命令执行成功！"
        break
    else
        ((retry_count++))
        echo "命令执行失败 (退出码: $exit_status)"
        
        # 检查是否超过最大重试次数
        if [ $MAX_RETRIES -ne 0 ] && [ $retry_count -ge $MAX_RETRIES ]; then
            echo "已达到最大重试次数 ($MAX_RETRIES)，停止重试。"
            exit 1
        fi
        
        echo "等待 $RETRY_DELAY 秒后重试 (尝试: $retry_count)..."
        sleep $RETRY_DELAY
    fi
done

echo "任务完成！"
