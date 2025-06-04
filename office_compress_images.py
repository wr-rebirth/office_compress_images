from os import mkdir
from os.path import abspath, basename, exists, expanduser, getsize, join
from shutil import move, rmtree
from subprocess import DEVNULL, run
from PIL import Image
import os

# 缓存文件夹路径
cache_folder = expanduser("~/Library/Caches/compress-office/")

def convert_size(size_in_byte: int) -> str:
    units = ("B", "KB", "MB", "GB")
    for unit in units:
        if size_in_byte < 1024:
            return f"{round(size_in_byte, 2)}{unit}"
        size_in_byte /= 1024
    return f"{round(size_in_byte, 2)}TB"

def compress_image(image_path: str) -> None:
    """快速压缩单个图片"""
    try:
        img = Image.open(image_path)
        before_size = getsize(image_path)
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(image_path, 'JPEG', quality=85, optimize=True)
        after_size = getsize(image_path)
        print(f"  正在压缩 {basename(image_path)}: {convert_size(before_size)} -> {convert_size(after_size)}")
    except Exception:
        pass

def compress(file_path: str) -> None:
    file_path = abspath(file_path)
    file_name = basename(file_path)
    before_size = getsize(file_path)

    # 清理并创建缓存文件夹
    if exists(cache_folder):
        rmtree(cache_folder)
    mkdir(cache_folder)

    # 解压文件
    print("正在解压文档...")
    run(["unzip", file_path, "-d", cache_folder], stdout=DEVNULL).check_returncode()

    # 压缩图片
    print("正在压缩图片...")
    for root, _, files in os.walk(cache_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = join(root, file)
                compress_image(image_path)

    # 重新打包
    print("正在重新打包...")
    new_file_path = join(cache_folder, file_name)
    run(["zip", file_name, "-r", "."], stdout=DEVNULL, cwd=cache_folder).check_returncode()
    
    after_size = getsize(new_file_path)
    if after_size >= before_size:
        print("文件大小未发生变化")
        return

    # 替换原文件
    run(["trash", file_path]).check_returncode()
    move(new_file_path, file_path)

    # 清理缓存
    if exists(cache_folder):
        rmtree(cache_folder)

    print(f"压缩完成: {convert_size(before_size)} -> {convert_size(after_size)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("使用方法: python function.py <文件路径>")
        sys.exit(1)
    compress(sys.argv[1].strip('"').replace("\\", "/"))
