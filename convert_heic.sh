#!/bin/bash

# 檢查是否安裝了 magick 或 convert 指令
if ! command -v magick &> /dev/null && ! command -v convert &> /dev/null; then
    echo "錯誤: 未偵測到 ImageMagick，請先安裝它。"
    echo "Mac 使用者請執行: brew install imagemagick"
    echo "Ubuntu 使用者請執行: sudo apt install imagemagick"
    exit 1
fi

echo "開始搜尋並轉換 HEIC 檔案..."
echo "----------------------------------------"

# 計數器
count=0

# 使用 find 尋找目前目錄及子目錄下的所有 .heic 或 .HEIC 檔案
# -print0 和 read -d $'\0' 可以完美處理檔名包含空格的情況
find . -type f \( -iname "*.heic" \) -print0 | while IFS= read -r -d $'\0' file; do
    # 取得不含副檔名的路徑與檔名
    filename="${file%.*}"
    
    echo "正在轉換: $file -> ${filename}.png"
    
    # 執行轉換（優先使用新版 ImageMagick 的 magick 指令，舊版則用 convert）
    if command -v magick &> /dev/null; then
        magick "$file" "${filename}.png"
    else
        convert "$file" "${filename}.png"
    fi
    
    # 如果你想在轉換成功後「刪除原來的 HEIC 檔」，請把下面那行的 # 拿掉
    # rm "$file"

    ((count++))
done

echo "----------------------------------------"
echo "轉換完成！共轉換了 $count 個檔案。"