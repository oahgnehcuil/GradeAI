#!/bin/bash

# 使用 "." 代表當前目錄，遞迴搜尋所有子資料夾
find . -type f -iname "*.heic" | while read -r heic_path; do
    base_path="${heic_path%.*}"
    pdf_path="${base_path}.pdf"
    
    if [ ! -f "$pdf_path" ]; then
        echo "正在轉換: $heic_path"
        sips -s format pdf "$heic_path" --out "$pdf_path" > /dev/null 2>&1
    fi
done

echo "轉換完成！"