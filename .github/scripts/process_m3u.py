import os
import requests
import re
from datetime import datetime
from pathlib import Path

def download_m3u(source_url):
    """下载M3U源文件"""
    try:
        response = requests.get(source_url, timeout=25)
        response.encoding = 'utf-8'
        response.raise_for_status()
        print(f"✅ M3U文件下载成功，长度: {len(response.text)}字符")
        return response.text
    except requests.RequestException as e:
        print(f"❌ 下载失败: {str(e)}")
        return None

def clean_content(content):
    """
    清理M3U内容：
    1. 移除无效条目
    2. 修复分组名称
    3. 过滤过期链接
    """
    valid_lines = []
    channels_count = 0
    group_name_map = {}
    current_group = ""
    
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
            
        # 保留文件头
        if line.startswith("#EXTM3U"):
            valid_lines.append(line)
            continue
            
        # 处理扩展信息行
        if line.startswith("#EXTINF"):
            # 提取分组名称
            group_match = re.search(r'group-title="([^"]+)"', line)
            tvg_name_match = re.search(r'tvg-name="([^"]+)"', line)
            channel_name = tvg_name_match.group(1) if tvg_name_match else "Unknown"
            
            if group_match:
                current_group = group_match.group(1)
                # 简化分组名称
                clean_group = re.sub(r'[\|\[\]()]+', '', current_group).strip()
                clean_group = re.sub(r'\s{2,}', ' ', clean_group)
                
                # 更新行中的分组名称
                line = line.replace(f'group-title="{current_group}"', f'group-title="{clean_group}"')
                current_group = clean_group
                
                # 统计分组
                group_name_map[clean_group] = group_name_map.get(clean_group, 0) + 1
            
            valid_lines.append(line)
            continue
            
        # 处理URL行
        if line.startswith("http"):
            # 过滤非媒体链接
            if ".php" in line or ".html" in line or "=" in line:
                continue
                
            valid_lines.append(line)
            channels_count += 1
            
    # 输出统计信息
    print(f"📊 频道总数: {channels_count}")
    print(f"📁 分组统计: {len(group_name_map)}个分组")
    
    # 只保留最活跃的分组
    active_groups = [group for group, count in group_name_map.items() if count >= 3]
    if active_groups:
        print(f"🏷️ 活跃分组: {', '.join(sorted(active_groups)[:10])}...")
    
    return "\n".join(valid_lines)

def save_m3u(content, output_dir):
    """保存处理后的M3U文件"""
    try:
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"cleaned_m3u_{timestamp}.m3u"
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"💾 文件保存成功: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ 文件保存失败: {str(e)}")
        return None

def main():
    source_url = os.getenv("SOURCE_URL")
    if not source_url:
        print("❌ 错误: SOURCE_URL环境变量未设置")
        return
        
    print(f"🔗 源URL: {source_url}")
    
    # 设置输出目录
    output_dir = Path.cwd() / "generated"
    
    # 下载并处理M3U
    content = download_m3u(source_url)
    if not content:
        return
        
    # 清理内容
    print("🧹 开始清理内容...")
    cleaned_content = clean_content(content)
    
    # 保存文件
    save_m3u(cleaned_content, output_dir)
    print("🎉 处理完成!")

if __name__ == "__main__":
    main()
