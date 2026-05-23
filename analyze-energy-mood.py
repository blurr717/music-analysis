# -*- coding: utf-8 -*-
"""
分析 MP3 音频文件的能量（Energy）与情绪（Mood）
使用 librosa 提取频谱特征并生成可视化图表
"""

import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # 非交互式后端，直接保存图片

# ============================================================
# 配置
# ============================================================
# 使用支持中文的字体（Windows 微软雅黑）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

AUDIO_PATH = "c:/Users/Administrator/Downloads/Camila Cabello - DREAM-GIRLS.mp3"
OUTPUT_PATH = "C:/Users/Administrator/Desktop/daima/dream-girls-analysis/dream-girls-summary.png"
SR = 22050  # 重采样率

def fmt_mmss(sec, _=None):
    """将秒数转为 m:ss 格式"""
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}:{s:02d}"

def set_time_axis(ax, duration_sec):
    """将坐标轴 x 轴设为 mm:ss 格式"""
    tick_secs = np.arange(0, duration_sec + 1, 10)
    ax.set_xticks(tick_secs)
    ax.set_xticklabels([fmt_mmss(t) for t in tick_secs], fontsize=8)
    ax.set_xlim(0, duration_sec)

print("=" * 60)
print("  DREAM-GIRLS — 能量与情绪分析")
print("=" * 60)

# ============================================================
# 1. 加载音频
# ============================================================
print("\n[1/5] 正在加载音频...")
y, sr = librosa.load(AUDIO_PATH, sr=SR, mono=True)
duration = librosa.get_duration(y=y, sr=sr)
print(f"  采样率: {sr} Hz")
print(f"  时长: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
print(f"  总采样点数: {len(y):,}")

# ============================================================
# 2. 提取能量特征
# ============================================================
print("\n[2/5] 正在提取能量特征...")

# RMS 能量（每帧）
rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
rms_mean = np.mean(rms)
rms_std = np.std(rms)
rms_db = librosa.amplitude_to_db(rms, ref=np.max)
rms_db_mean = np.mean(rms_db)

# 节奏（BPM）
tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
tempo = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)

# 频谱质心（声音明亮度）
spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
centroid_mean = np.mean(spectral_centroid)

# 过零率
zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=2048, hop_length=512)[0]
zcr_mean = np.mean(zcr)

# 频谱带宽
spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
bandwidth_mean = np.mean(spectral_bandwidth)

print(f"  RMS 能量均值: {rms_mean:.4f}")
print(f"  RMS 能量标准差: {rms_std:.4f}")
print(f"  RMS 均值 (dB): {rms_db_mean:.1f} dB")
print(f"  节奏 (BPM): {tempo:.1f}")
print(f"  频谱质心均值: {centroid_mean:.1f} Hz")
print(f"  过零率均值: {zcr_mean:.4f}")
print(f"  频谱带宽均值: {bandwidth_mean:.1f} Hz")

# ============================================================
# 3. 提取情绪特征
# ============================================================
print("\n[3/5] 正在提取情绪特征...")

# MFCC（20个系数）
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
mfcc_means = np.mean(mfcc, axis=1)

# 色度特征（12音高类别）
chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=12)
chroma_means = np.mean(chroma, axis=1)

# 频谱对比度
spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
contrast_means = np.mean(spectral_contrast, axis=1)

# 频谱通量（spectral flux，衡量频谱变化速度）
spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
spectral_flux = np.mean(np.diff(spec, axis=1) ** 2, axis=0)
flux_mean = np.mean(spectral_flux)

# RMS 能量方差（反映动态变化）
rms_variance = np.var(rms)

print(f"  MFCC 均值范围: [{np.min(mfcc_means):.1f}, {np.max(mfcc_means):.1f}]")
print(f"  频谱通量均值: {flux_mean:.6f}")
print(f"  RMS 方差: {rms_variance:.6f}")

# ============================================================
# 4. 计算能量与情绪得分
# ============================================================
print("\n[4/5] 正在计算综合得分...")

# --- 能量得分 (0-1) ---
# 使用多个特征归一化后加权平均

def normalize(value, low, high):
    """将值归一化到 [0,1] 区间"""
    return np.clip((value - low) / (high - low), 0, 1)

# RMS 归一化：典型音乐 RMS 范围约 0.01 ~ 0.3
rms_score = normalize(rms_mean, 0.01, 0.25)

# 节奏归一化：慢歌 60 BPM → 快歌 180 BPM
tempo_score = normalize(tempo, 60, 180)

# 频谱质心归一化：暗 500 Hz → 亮 4000 Hz
centroid_score = normalize(centroid_mean, 500, 4000)

# 过零率归一化
zcr_score = normalize(zcr_mean, 0.02, 0.15)

# 频谱通量归一化（动态越大 → 能量越高）
flux_score = normalize(flux_mean, 0, 0.01)

# 综合能量得分
energy_score = (
    rms_score * 0.30 +
    tempo_score * 0.25 +
    centroid_score * 0.20 +
    zcr_score * 0.15 +
    flux_score * 0.10
)

# --- 情绪效价得分 (Valence, 0-1) ---
# 使用色度特征判断大调/小调倾向
# 大调和弦音高分：C=0, E=4, G=7；小调：C=0, Eb=3, G=7
major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])  # C大调音高分布
minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])  # C小调音高分布
major_corr = np.corrcoef(chroma_means, major_profile)[0, 1]
minor_corr = np.corrcoef(chroma_means, minor_profile)[0, 1]
mode_score = normalize(major_corr - minor_corr, -0.5, 0.5)

# MFCC 第2系数（通常与情绪效价相关）
mfcc2_score = normalize(mfcc_means[1], -200, 200)

# 频谱对比度第2频带（中频对比度）
contrast_mid_score = normalize(contrast_means[2], 10, 30)

valence_score = (
    mode_score * 0.40 +
    mfcc2_score * 0.35 +
    contrast_mid_score * 0.25
)

# --- 情绪唤醒度得分 (Arousal, 0-1) ---
# RMS方差 → 动态范围越大越紧张
rms_var_score = normalize(rms_variance, 0.0, 0.005)

# 频谱通量 → 频谱变化越快越兴奋
flux_arousal_score = normalize(flux_mean, 0.0, 0.005)

arousal_score = (
    energy_score * 0.40 +
    rms_var_score * 0.30 +
    flux_arousal_score * 0.30
)

# --- 情绪描述 ---
def describe_mood(valence, arousal):
    """根据效价和唤醒度给出情绪描述"""
    if valence > 0.6 and arousal > 0.6:
        return "兴奋/欢快 (Excited/Joyful)"
    elif valence > 0.6 and arousal <= 0.6:
        return "轻松/愉悦 (Relaxed/Content)"
    elif valence <= 0.4 and arousal > 0.6:
        return "紧张/愤怒 (Tense/Angry)"
    elif valence <= 0.4 and arousal <= 0.6:
        return "悲伤/忧郁 (Sad/Melancholic)"
    else:
        return "中性/平和 (Neutral/Calm)"

def describe_energy(score):
    """根据能量得分给出描述"""
    if score > 0.75:
        return "非常高 — 充满爆发力和动感"
    elif score > 0.55:
        return "较高 — 活泼有劲"
    elif score > 0.35:
        return "中等 — 有起伏但不极端"
    elif score > 0.15:
        return "较低 — 柔和舒缓"
    else:
        return "非常低 — 极简安静"

mood_label = describe_mood(valence_score, arousal_score)
energy_label = describe_energy(energy_score)

print(f"\n  {'─' * 40}")
print(f"  能量得分: {energy_score:.2f}/1.00 — {energy_label}")
print(f"  效价得分: {valence_score:.2f}/1.00")
print(f"  唤醒度得分: {arousal_score:.2f}/1.00")
print(f"  综合情绪: {mood_label}")
print(f"  {'─' * 40}")

# ============================================================
# 5. 生成可视化图表
# ============================================================
print("\n[5/5] 正在生成图表...")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle(f"《DREAM-GIRLS》— Camila Cabello\n"
             f"能量: {energy_score:.2f} | 效价: {valence_score:.2f} | "
             f"唤醒度: {arousal_score:.2f} | {mood_label}",
             fontsize=14, fontweight="bold")

# 时间轴
times = librosa.times_like(rms, sr=sr, hop_length=512)

# (a) 波形图 + RMS 能量叠加
ax = axes[0, 0]
# 将波形降采样到与 times 相同的长度
wave_down = np.interp(times, np.linspace(0, duration, len(y)), y)
ax.plot(times, wave_down, alpha=0.5, color="steelblue", linewidth=0.5, label="波形")
ax.plot(times, rms, color="crimson", linewidth=1.5, label="RMS 能量")
ax.set_title("波形与能量包络")
ax.set_xlabel("时间")
ax.set_ylabel("幅度 / RMS")
ax.legend(loc="upper right", fontsize=8)
set_time_axis(ax, duration)

# (b) RMS 能量 dB 分布直方图
ax = axes[0, 1]
ax.hist(rms_db, bins=60, color="coral", alpha=0.8, edgecolor="white")
ax.axvline(rms_db_mean, color="darkred", linestyle="--", linewidth=2,
           label=f"均值: {rms_db_mean:.1f} dB")
ax.set_title("RMS 能量分布 (dB)")
ax.set_xlabel("dB")
ax.set_ylabel("帧数")
ax.legend(fontsize=8)

# (c) 频谱图
ax = axes[0, 2]
D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=512)),
                            ref=np.max)
img = librosa.display.specshow(D, sr=sr, hop_length=512, x_axis="time",
                               y_axis="log", ax=ax, cmap="magma")
ax.set_title("频谱图 (Spectrogram)")
ax.set_xlabel("时间")
ax.set_ylabel("频率 (Hz)")
set_time_axis(ax, duration)
fig.colorbar(img, ax=ax, format="%+2.0f dB")

# (d) 色度图
ax = axes[1, 0]
chroma_full = librosa.feature.chroma_stft(y=y, sr=sr)
img = librosa.display.specshow(chroma_full, sr=sr, hop_length=512,
                               x_axis="time", y_axis="chroma", ax=ax,
                               cmap="coolwarm")
ax.set_title("色度图 (Chroma)")
ax.set_xlabel("时间")
ax.set_ylabel("音高类别")
set_time_axis(ax, duration)
fig.colorbar(img, ax=ax)

# (e) MFCC 热力图
ax = axes[1, 1]
img = librosa.display.specshow(mfcc, sr=sr, hop_length=512, x_axis="time",
                               ax=ax, cmap="coolwarm")
ax.set_title("MFCC 热力图")
ax.set_xlabel("时间")
ax.set_ylabel("MFCC 系数")
set_time_axis(ax, duration)
fig.colorbar(img, ax=ax)

# (f) 能量 & 情绪仪表盘
ax = axes[1, 2]
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-1.2, 1.2)
ax.set_aspect("equal")
ax.axhline(0, color="gray", linewidth=0.5)
ax.axvline(0, color="gray", linewidth=0.5)

# 画情绪象限
circle = plt.Circle((0, 0), 1, fill=False, color="gray", linewidth=1,
                    linestyle="--")
ax.add_patch(circle)

# 象限标签
ax.text(0.7, 0.7, "兴奋/欢快", ha="center", va="center", fontsize=10,
        color="green", fontweight="bold")
ax.text(-0.7, 0.7, "紧张/愤怒", ha="center", va="center", fontsize=10,
        color="red", fontweight="bold")
ax.text(0.7, -0.7, "轻松/愉悦", ha="center", va="center", fontsize=10,
        color="blue", fontweight="bold")
ax.text(-0.7, -0.7, "悲伤/忧郁", ha="center", va="center", fontsize=10,
        color="purple", fontweight="bold")

# 绘制当前歌曲位置
x = (arousal_score - 0.5) * 2  # 映射到 [-1, 1]
y = (valence_score - 0.5) * 2
ax.scatter(x, y, s=500, c="gold", edgecolors="black", linewidth=2,
           zorder=5)
ax.annotate("DREAM-GIRLS", (x, y), textcoords="offset points",
            xytext=(0, 15), ha="center", fontsize=10, fontweight="bold",
            color="darkorange")

ax.set_title("情绪象限 (效价 × 唤醒度)")
ax.set_xlabel("唤醒度 (Arousal) ← 低 | 高 →")
ax.set_ylabel("效价 (Valence) ← 负 | 正 →")
ax.set_xticks([])
ax.set_yticks([])

plt.tight_layout()
fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)

print(f"  图表已保存至: {OUTPUT_PATH}")
print(f"\n{'=' * 60}")
print("  分析完成！")
print(f"{'=' * 60}")
