#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国大学生计算机设计大赛（2026版）源码打包脚本
功能：整理项目源码，排除编译文件/开源库，保留自主开发代码和样本数据
输出：xuezhi-portrait-source.zip
"""

import os
import sys
import shutil
import zipfile
import glob
import fnmatch
from pathlib import Path

# 项目根目录
ROOT = Path(r"d:\桌面\xuezhi-portrait-master")
# 输出目录
OUTPUT_DIR = ROOT / "_competition_package"
OUTPUT_ZIP = ROOT / "xuezhi-portrait-source.zip"
ZIP_INNER_DIR = "xuezhi-portrait-source"  # ZIP内层目录名

# ============================================================
# 排除规则
# ============================================================
EXCLUDE_PATTERNS = [
    # 编译中间文件
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.pyd",
    
    # 数据库文件
    "**/instance/**",
    "**/*.db",
    "**/*.sqlite",
    "**/*.sqlite3",
    
    # 开源/公共库代码 (Docker部署配置不属于自主开发源码)
    "Dockerfile",
    "docker-compose.yml",
    ".dockerignore",
    "nginx.conf",
    
    # NPM/Node (本项目无实质npm依赖)
    "package.json",
    "**/node_modules/**",
    "package-lock.json",
    
    # 部署/构建辅助文件
    "install.bat",
    "start.bat",
    "deploy_to_server.sh",
    
    # 大型生成物 - outputs目录中只保留build_a3_deck.py和设计文稿
    # 排除output/preview目录下的预览图片
    "outputs/**/output/preview/**",
    # 排除生成的PPTX文件
    "outputs/**/output/*.pptx",
    # 输出目录中的图片
    "outputs/**/*.png",
    "outputs/**/*.jpg",
    "outputs/**/*.jpeg",
    
    # 冗余的变更记录markdown (保留README和QUICK_START即可)
    "CHANGES_INTELLIGENT_ASSISTANT.md",
    "HTML_RENDER_FIX.md",
    "IMPLEMENTATION_SUMMARY.md",
    "KNOWLEDGE_QA_DEMO.md",
    "KNOWLEDGE_QA_IMPLEMENTATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "README_MODIFICATION.md",
    "DEBUG_MANUAL.md",
    "TESTING_GUIDE.md",
    
    # 其他非核心文件
    "debug_knowledge_api.py",
    "DOCUMENTATION_INDEX.md",
    "take_screenshots.py",  # 截图工具，非核心源码
    "test_knowledge_simple.py",  # 调试测试，非正式测试
    "test_resume_api.py",       # API调试脚本
    "RESUME_GENERATION_GUIDE.md",  # 功能使用说明，非工程设计文档
    "RESUME_TROUBLESHOOTING_GUIDE.md",
    "UI_PREVIEW.md",
    "UPDATE_API_INTEGRATION.md",
    
    # IDE/编辑器文件
    "**/.vscode/**",
    "**/.idea/**",
    "**/.DS_Store",
    "**/Thumbs.db",
    
    # 环境/虚拟环境
    "**/venv/**",
    "**/.venv/**",
    "**/env/**",
    
    # 打包临时文件
    "_competition_package/**",
    "pack_for_competition.py",
    "create_summary_table.py",
    "node_modules/**",
    "package-lock.json",
]

# ============================================================
# 截图保留规则：只保留3-5张代表性截图
# ============================================================
KEEP_SCREENSHOTS = [
    "homepage.png",           # 首页
    "intelligent_assistant_fixed.png",  # 智能助手
    "student_portrait.png",   # 学生画像 (或assessment)
    "learning_plan_fixed.png",  # 学习计划
]

# docs/evidence中的截图完全排除 (与screenshots/重复)
EXCLUDE_PATTERNS.append("docs/evidence/screenshots/**")

# ============================================================
# 主打包逻辑
# ============================================================

def should_exclude(rel_path):
    """判断文件/目录是否应该被排除 (使用 fnmatch 进行 glob 匹配)"""
    rel_str = rel_path.replace(os.sep, "/") if isinstance(rel_path, Path) else rel_path.replace(os.sep, "/")
    basename = os.path.basename(rel_str)
    
    for pattern in EXCLUDE_PATTERNS:
        # 精确匹配（全路径或仅文件名）
        if pattern == rel_str or pattern == basename:
            return True
        # 用 fnmatch 进行 glob 匹配 (比 Path.match 更可靠，尤其是含中文路径时)
        if "*" in pattern or "?" in pattern:
            if fnmatch.fnmatch(rel_str, pattern):
                return True
            # 也尝试匹配 basename
            if fnmatch.fnmatch(basename, pattern):
                return True
    return False


def should_keep_screenshot(filename):
    """判断截图是否保留"""
    if filename in KEEP_SCREENSHOTS:
        return True
    # 保留所有非占位图(>40KB)中最小的几张，总数不超过5张
    return False


def copy_with_filter(src_root, dst_root):
    """带过滤的文件复制"""
    # 先清理输出目录
    if dst_root.exists():
        shutil.rmtree(str(dst_root))
    
    src_root = Path(src_root)
    dst_root = Path(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    skipped_count = 0
    
    # 收集所有截图文件（用于特殊处理）
    screenshot_files_to_keep = set()
    
    for root, dirs, files in os.walk(str(src_root)):
        root_path = Path(root)
        rel_dir = str(root_path.relative_to(src_root))
        
        # 跳过排除的目录
        dirs_to_remove = []
        for d in dirs:
            d_rel = os.path.join(rel_dir, d).replace("\\", "/")
            if d_rel == ".":
                d_rel = d
            if should_exclude(d_rel):
                dirs_to_remove.append(d)
                skipped_count += 1
        for d in dirs_to_remove:
            dirs.remove(d)
        
        for f in files:
            f_rel = os.path.join(rel_dir, f).replace("\\", "/")
            if f_rel.startswith("./"):
                f_rel = f_rel[2:]
            elif f_rel == ".":
                f_rel = f
            
            if should_exclude(f_rel):
                skipped_count += 1
                continue
            
            # 特殊处理：screenshots目录下的文件
            if rel_dir.startswith("screenshots") or rel_dir.startswith("screenshots"):
                if not should_keep_screenshot(f):
                    skipped_count += 1
                    continue
            
            # 复制文件
            src_file = root_path / f
            rel_file_path = os.path.join(rel_dir, f)
            dst_file = dst_root / rel_file_path
            
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src_file), str(dst_file))
            copied_count += 1
    
    print(f"  复制文件: {copied_count} 个")
    print(f"  排除项: {skipped_count} 个")
    return copied_count


def create_sample_quiz_csv(src_csv, dst_csv, n_rows=50):
    """从完整quiz_data.csv中提取样本行"""
    if not Path(src_csv).exists():
        print(f"  警告: quiz_data.csv 不存在: {src_csv}")
        return
    
    with open(src_csv, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    header = lines[0] if lines else ""
    # 保留表头和前n_rows行数据
    sample_lines = lines[:min(n_rows + 1, len(lines))]
    
    with open(dst_csv, "w", encoding="utf-8") as f:
        f.writelines(sample_lines)
    
    print(f"  生成样本数据集: {dst_csv} ({len(sample_lines) - 1} 行数据)")


def rename_quiz_csv():
    """将quiz_data.csv重命名为quiz_data_sample.csv并添加说明"""
    pass  # 通过copy_with_filter处理，之后在ZIP中统一处理


def main():
    print("=" * 60)
    print("中国大学生计算机设计大赛（2026版）源码打包工具")
    print("=" * 60)
    
    # Step 1: 清理旧文件
    print("\n[1/4] 清理旧输出...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(str(OUTPUT_DIR))
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    print("  完成")
    
    # Step 2: 复制过滤后的文件
    print("\n[2/4] 复制源代码文件（过滤中）...")
    copy_with_filter(ROOT, OUTPUT_DIR / ZIP_INNER_DIR)
    
    # Step 3: 处理 quiz_data.csv - 保留前50行作为样本
    print("\n[3/4] 处理数据集样本...")
    src_quiz = OUTPUT_DIR / ZIP_INNER_DIR / "quiz_data.csv"
    if src_quiz.exists():
        # 读取完整csv，只保留前50行
        with open(src_quiz, "r", encoding="utf-8") as f:
            lines = f.readlines()
        sample_lines = lines[:min(51, len(lines))]
        src_quiz.unlink()
        dst_quiz = OUTPUT_DIR / ZIP_INNER_DIR / "quiz_data_sample.csv"
        with open(dst_quiz, "w", encoding="utf-8") as f:
            f.writelines(sample_lines)
        print(f"  生成样本数据集: quiz_data_sample.csv ({len(sample_lines)-1} 行数据)")
    
    # Step 4: 创建ZIP压缩包
    print(f"\n[4/4] 生成ZIP压缩包: {OUTPUT_ZIP.name}")
    
    def zipdir(path, zipf, base_path):
        for root, dirs, files in os.walk(str(path)):
            for f in files:
                file_path = Path(root) / f
                arcname = str(file_path.relative_to(base_path))
                zipf.write(str(file_path), arcname)
    
    with zipfile.ZipFile(str(OUTPUT_ZIP), "w", zipfile.ZIP_DEFLATED) as zipf:
        zipdir(OUTPUT_DIR / ZIP_INNER_DIR, zipf, OUTPUT_DIR)
    
    # 统计大小
    zip_size = OUTPUT_ZIP.stat().st_size
    print(f"  压缩完成!")
    print(f"  压缩包路径: {OUTPUT_ZIP}")
    print(f"  压缩包大小: {zip_size / 1024 / 1024:.2f} MB")
    
    # Step 5: 输出文件清单
    print("\n" + "=" * 60)
    print("打包完成！包含以下模块：")
    print("=" * 60)
    
    top_dirs = sorted([d.name for d in (OUTPUT_DIR / ZIP_INNER_DIR).iterdir() if d.is_dir()])
    top_files = sorted([f.name for f in (OUTPUT_DIR / ZIP_INNER_DIR).iterdir() if f.is_file()])
    
    print("\n[顶层目录]:")
    for d in top_dirs:
        print(f"  +-- {d}/")
    print("\n[顶层文件]:")
    for f in top_files:
        print(f"  +-- {f}")
    
    # 清理临时目录
    print(f"\n清理临时目录...")
    shutil.rmtree(str(OUTPUT_DIR))
    print("完成! 最终产物: xuezhi-portrait-source.zip")
    
    # 校验
    if zip_size > 200 * 1024 * 1024:
        print(f"\n[WARNING] ZIP文件大小超过200MB限制! ({zip_size/1024/1024:.2f} MB)")
    else:
        print(f"\n[OK] ZIP文件大小在200MB以内 ({zip_size/1024/1024:.2f} MB)，可直接上传。")


if __name__ == "__main__":
    main()
