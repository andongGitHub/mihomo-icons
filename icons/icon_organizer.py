import os
import shutil
import hashlib
from PIL import Image
import imagehash
from collections import defaultdict
import argparse

def calculate_image_hash(image_path):
    """计算图像的感知哈希值"""
    try:
        img = Image.open(image_path)
        # 使用感知哈希算法
        hash_value = str(imagehash.phash(img))
        return hash_value
    except Exception as e:
        print(f"处理图像 {image_path} 时出错: {e}")
        return None

def calculate_file_md5(file_path):
    """计算文件的MD5哈希值"""
    try:
        with open(file_path, 'rb') as f:
            md5_hash = hashlib.md5()
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        print(f"计算文件 {file_path} 的MD5时出错: {e}")
        return None

def is_image_file(file_path):
    """检查文件是否为图像文件"""
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg']
    _, ext = os.path.splitext(file_path)
    return ext.lower() in image_extensions

def organize_icons(root_dir, output_dir, similarity_threshold=2):
    """
    整理图标文件
    
    参数:
    root_dir: 要扫描的根目录
    output_dir: 输出目录
    similarity_threshold: 感知哈希相似度阈值
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 存储所有图像文件的路径
    all_images = []
    
    # 扫描所有图像文件
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if is_image_file(file_path):
                all_images.append(file_path)
    
    print(f"找到 {len(all_images)} 个图像文件")
    
    # 按MD5哈希值分组
    md5_groups = defaultdict(list)
    for image_path in all_images:
        md5_hash = calculate_file_md5(image_path)
        if md5_hash:
            md5_groups[md5_hash].append(image_path)
    
    # 处理完全相同的文件（MD5相同）
    unique_images = []
    duplicate_count = 0
    
    for md5_hash, file_paths in md5_groups.items():
        unique_images.append(file_paths[0])
        duplicate_count += len(file_paths) - 1
    
    print(f"找到 {duplicate_count} 个完全相同的文件（MD5相同）")
    
    # 按感知哈希分组处理相似图像
    phash_groups = defaultdict(list)
    for image_path in unique_images:
        phash = calculate_image_hash(image_path)
        if phash:
            phash_groups[phash].append(image_path)
    
    # 处理相似图像
    similar_groups = []
    processed_hashes = set()
    
    for phash, file_paths in phash_groups.items():
        if phash in processed_hashes:
            continue
        
        similar_group = file_paths.copy()
        processed_hashes.add(phash)
        
        # 查找相似的哈希值
        for other_phash, other_file_paths in phash_groups.items():
            if other_phash != phash and other_phash not in processed_hashes:
                # 计算汉明距离
                hamming_distance = sum(c1 != c2 for c1, c2 in zip(phash, other_phash))
                if hamming_distance <= similarity_threshold:
                    similar_group.extend(other_file_paths)
                    processed_hashes.add(other_phash)
        
        if len(similar_group) > 1:
            similar_groups.append(similar_group)
    
    # 创建分类目录
    unique_dir = os.path.join(output_dir, "unique_icons")
    similar_dir = os.path.join(output_dir, "similar_groups")
    
    if not os.path.exists(unique_dir):
        os.makedirs(unique_dir)
    
    if not os.path.exists(similar_dir):
        os.makedirs(similar_dir)
    
    # 复制唯一图标
    unique_count = 0
    for phash, file_paths in phash_groups.items():
        if len(file_paths) == 1 and phash not in processed_hashes:
            src_path = file_paths[0]
            filename = os.path.basename(src_path)
            dst_path = os.path.join(unique_dir, filename)
            
            # 处理文件名冲突
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(filename)
                dst_path = os.path.join(unique_dir, f"{base}_{unique_count}{ext}")
            
            shutil.copy2(src_path, dst_path)
            unique_count += 1
    
    # 复制相似图标组
    for i, group in enumerate(similar_groups):
        group_dir = os.path.join(similar_dir, f"group_{i+1}")
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)
        
        for j, file_path in enumerate(group):
            filename = os.path.basename(file_path)
            dst_path = os.path.join(group_dir, filename)
            
            # 处理文件名冲突
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(filename)
                dst_path = os.path.join(group_dir, f"{base}_{j}{ext}")
            
            shutil.copy2(file_path, dst_path)
    
    print(f"整理完成！")
    print(f"- 唯一图标: {unique_count} 个")
    print(f"- 相似图标组: {len(similar_groups)} 组")
    print(f"结果保存在: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图标文件归类和去重工具")
    parser.add_argument("--input", default="d:\\Icon-for-webui-main", help="输入目录路径")
    parser.add_argument("--output", default="d:\\Icon-for-webui-main\\organized_icons", help="输出目录路径")
    parser.add_argument("--threshold", type=int, default=2, help="图像相似度阈值（汉明距离）")
    
    args = parser.parse_args()
    
    organize_icons(args.input, args.output, args.threshold)