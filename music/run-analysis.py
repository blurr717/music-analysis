# -*- coding: utf-8 -*-
"""
音乐分析主入口脚本
用法: python run-analysis.py <音频文件路径> [选项]

自动完成以下操作：
1. 从文件名提取歌曲名
2. 在 music-analysis/ 下创建 <歌曲名-analysis>/ 目录
3. 复制原始音频到该目录
4. 依次运行能量/情绪分析和时间曲线分析
"""

import argparse
import importlib
import os
import re
import shutil
import sys
from pathlib import Path

# 确保可以导入同目录下的分析模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 项目根目录（脚本所在目录）
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = PROJECT_ROOT / "music-analysis"

# 支持的音频格式
SUPPORTED_FORMATS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}


def slugify(text):
    """
    将歌曲名转换为文件系统安全的目录名。
    "DREAM-GIRLS" → "dream-girls"
    "Amor, que pena!" → "amor-que-pena"
    """
    # 转小写
    text = text.lower()
    # 将各种分隔符和标点替换为连字符
    text = re.sub(r"[\s,.;:!?()（）【】\[\]{}'\"/\\|@#$%^&*+=~`]+", "-", text)
    # 合并连续的连字符
    text = re.sub(r"-{2,}", "-", text)
    # 去掉首尾连字符
    text = text.strip("-")
    # 空字符串兜底
    return text or "untitled"


def extract_song_name(filepath):
    """
    从文件路径提取歌曲名。

    规则：
    1. 取文件名（不含扩展名）
    2. 如果包含 " - "，取后半部分作为歌曲名
    3. 否则使用整个文件名
    """
    stem = Path(filepath).stem.strip()
    if not stem:
        return None
    # 按 " - " 分割，取最后一部分
    parts = stem.rsplit(" - ", 1)
    if len(parts) == 2:
        # 前半部分是艺术家，后半部分是歌曲名
        return parts[1].strip(), parts[0].strip()
    return stem, None


def validate_file(filepath):
    """验证输入文件。返回 (Path, error_message)"""
    path = Path(filepath)
    if not path.exists():
        return None, f"文件不存在: {filepath}"
    if not path.is_file():
        return None, f"路径不是文件: {filepath}"
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        print(f"⚠ 警告: 文件格式 \"{suffix}\" 可能不被支持，将尝试加载...")
    return path, None


def main():
    parser = argparse.ArgumentParser(
        description="音乐分析 — 一键完成能量/情绪分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run-analysis.py "C:/Downloads/Camila Cabello - DREAM-GIRLS.mp3"
  python run-analysis.py song.mp3 --artist "Camila Cabello" --song-title "DREAM-GIRLS"
  python run-analysis.py song.mp3 --copy --skip-curves
        """,
    )
    parser.add_argument("audio_file", help="音频文件路径 (mp3, wav, flac 等)")
    parser.add_argument("--artist", "-a", default=None, help="艺术家名称（默认从文件名自动推断）")
    parser.add_argument("--song-title", "-t", default=None, help="歌曲名称（默认从文件名自动提取）")
    parser.add_argument("--copy", action="store_true", help="复制原始音频到输出目录（默认不复制）")
    parser.add_argument("--skip-summary", action="store_true", help="跳过能量/情绪综合分析")
    parser.add_argument("--skip-curves", action="store_true", help="跳过时间曲线分析")
    parser.add_argument("--output-dir", "-o", default=None, help="输出根目录 (默认: music-analysis/)")
    args = parser.parse_args()

    # ---- 1. 验证输入文件 ----
    filepath, error = validate_file(args.audio_file)
    if error:
        print(f"❌ 错误: {error}", file=sys.stderr)
        sys.exit(1)

    # ---- 2. 提取歌曲名和艺术家 ----
    if args.song_title:
        song_title = args.song_title
        artist = args.artist
    else:
        result = extract_song_name(str(filepath))
        if result is None:
            print("❌ 错误: 无法从文件名提取歌曲名，请使用 --song-title 指定", file=sys.stderr)
            sys.exit(1)
        song_title, auto_artist = result
        artist = args.artist or auto_artist

    song_slug = slugify(song_title)
    artist_str = f" — {artist}" if artist else ""

    print(f"\n🎵 歌曲: {song_title}{artist_str}")
    print(f"📁 文件: {filepath}")
    print(f"📂 输出目录: {song_slug}-analysis/")

    # ---- 3. 确定输出目录 ----
    output_root = Path(args.output_dir) if args.output_dir else OUTPUT_ROOT
    song_dir = output_root / f"{song_slug}-analysis"

    # ---- 4. 创建输出目录 ----
    try:
        song_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 输出目录已创建: {song_dir}")
    except OSError as e:
        print(f"❌ 错误: 无法创建输出目录 {song_dir}: {e}", file=sys.stderr)
        sys.exit(4)

    # ---- 5. 复制原始音频（仅当 --copy 时） ----
    if args.copy:
        try:
            dst_file = song_dir / filepath.name
            if dst_file.exists() and dst_file.samefile(filepath):
                print(f"ℹ 源文件和目标相同，跳过复制")
            else:
                shutil.copy2(filepath, dst_file)
                print(f"✅ 音频已复制到: {dst_file}")
        except OSError as e:
            print(f"⚠ 警告: 文件复制失败 ({e})，继续进行分析...")

    # ---- 6. 运行分析 ----
    results = {}

    if not args.skip_summary:
        print(f"\n{'─' * 60}")
        print("  [1/2] 能量与情绪综合分析")
        print(f"{'─' * 60}")
        energy_mod = importlib.import_module("analyze-energy-mood")
        analyze_energy_mood = energy_mod.analyze_energy_mood
        summary_path = str(song_dir / f"{song_slug}-summary.png")
        try:
            results["summary"] = analyze_energy_mood(
                audio_path=str(filepath),
                output_path=summary_path,
                song_title=song_title,
                artist=artist,
            )
        except Exception as e:
            print(f"❌ 错误: 综合分析失败: {e}", file=sys.stderr)
            results["summary"] = None

    if not args.skip_curves:
        print(f"\n{'─' * 60}")
        print("  [2/2] 时间曲线分析")
        print(f"{'─' * 60}")
        curves_mod = importlib.import_module("analyze-curves")
        analyze_curves = curves_mod.analyze_curves
        curves_path = str(song_dir / f"{song_slug}-curves.png")
        try:
            results["curves"] = analyze_curves(
                audio_path=str(filepath),
                output_path=curves_path,
                song_title=song_title,
                artist=artist,
            )
        except Exception as e:
            print(f"❌ 错误: 曲线分析失败: {e}", file=sys.stderr)
            results["curves"] = None

    # ---- 7. 综合摘要 ----
    print(f"\n{'=' * 60}")
    print(f"  ✅ 分析完成！")
    print(f"{'=' * 60}")
    print(f"  输出目录: {song_dir}")
    if results.get("summary"):
        r = results["summary"]
        print(f"  能量得分: {r['energy_score']:.2f}  — {r['energy_label']}")
        print(f"  效价得分: {r['valence_score']:.2f}")
        print(f"  唤醒度:   {r['arousal_score']:.2f}")
        print(f"  综合情绪: {r['mood_label']}")
        print(f"  BPM:      {r['tempo_bpm']:.0f}")
    if results.get("curves"):
        r = results["curves"]
        print(f"  能量均值: {r['energy_mean']:.3f}")
        print(f"  效价均值: {r['valence_mean']:.3f}")
        print(f"  唤醒度均值: {r['arousal_mean']:.3f}")
        print(f"  情绪走势: {r['mood_trend']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
