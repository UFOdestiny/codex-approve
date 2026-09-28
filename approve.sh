#!/usr/bin/env bash

TARGET="tarc:0.0"
waiting=0

while sleep 10; do
    # 只看当前可见内容，避免历史输出里的旧提示被重复匹配
    screen="$(tmux capture-pane -p -t "$TARGET")"

    approve=0
    reason=""

    # 1. 任何 retry without sandbox
    if grep -Fq 'Would you like to make the following edits?' <<< "$screen" &&
       grep -Fqi 'retry without sandbox?' <<< "$screen" &&
       grep -Fq 'Yes, proceed (y)' <<< "$screen"
    then
        approve=1
        reason="retry without sandbox"

    # 2. 普通 command approval
    elif grep -qE \
        'Would you like to run the following command\?|needs your approval' \
        <<< "$screen" &&
         grep -qE \
        'Yes, proceed|Yes, provide the requested info' \
        <<< "$screen"
    then
        approve=1
        reason="normal approval"
    fi

    if [ "$approve" -eq 1 ]; then
        if [ "$waiting" -eq 0 ]; then
            echo "[$(date '+%F %T')] auto approve: $reason"
            tmux send-keys -t "$TARGET" y
            waiting=1
        fi
    else
        waiting=0
    fi
done
