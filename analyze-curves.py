# -*- coding: utf-8 -*-
"""
分析 MP3 的能量与情绪随时间变化的曲线
将歌曲按秒分段，逐段计算能量、效价、唤醒度
"""

import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

AUDIO_PATH = "c:/Users/Administrator/Downloads/Camila Cabello - DREAM-GIRLS.mp3"
OUTPUT_PATH = "C:/Users/Administrator/Desktop/daima/dream-girls-analysis/dream-girls-curves.png"
SR = 22050
SEGMENT_SEC = 2  # 每段2秒

def fmt_mmss(sec, _=None):
    """将秒数转为 m:ss 格式"""
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}:{s:02d}"

def set_time_axis(ax, duration_sec):
    """将坐标轴 x 轴设为 mm:ss 格式"""
    import matplotlib.ticker as ticker
    # 每30秒一个刻度
    tick_secs = np.arange(0, duration_sec + 1, 10)
    ax.set_xticks(tick_secs)
    ax.set_xticklabels([fmt_mmss(t) for t in tick_secs], fontsize=8)
    ax.set_xlim(0, duration_sec)

print("=" * 60)
print("  DREAM-GIRLS — 能量与情绪时间曲线分析")
print("=" * 60)

# ============================================================
# 1. 加载音频
# ============================================================
print("\n[1/4] 正在加载音频...")
y, sr = librosa.load(AUDIO_PATH, sr=SR, mono=True)
duration = librosa.get_duration(y=y, sr=sr)
print(f"  采样率: {sr} Hz | 时长: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")

# ============================================================
# 2. 提取帧级特征
# ============================================================
print("\n[2/4] 正在提取帧级特征...")
hop_length = 512
frame_length = 2048
n_frames = 1 + (len(y) - frame_length) // hop_length

# RMS 能量（每帧）
rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

# 频谱质心
centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=frame_length,
                                             hop_length=hop_length)[0]

# 过零率
zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=frame_length,
                                         hop_length=hop_length)[0]

# MFCC
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=frame_length,
                            hop_length=hop_length)

# 色度
chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=12, n_fft=frame_length,
                                     hop_length=hop_length)

# 频谱对比度
contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_fft=frame_length,
                                             hop_length=hop_length)

# 频谱（用于计算频谱通量）
spec = np.abs(librosa.stft(y, n_fft=frame_length, hop_length=hop_length))

# 帧时间轴
times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop_length)

# 全局节奏
tempo_global, _ = librosa.beat.beat_track(y=y, sr=sr)
tempo_global = float(tempo_global.item()) if hasattr(tempo_global, 'item') else float(tempo_global)
print(f"  全局 BPM: {tempo_global:.1f} | 总帧数: {n_frames:,}")

# ============================================================
# 3. 分段计算能量与情绪得分
# ============================================================
print("\n[3/4] 正在分段计算能量/情绪曲线...")

frames_per_segment = int(SEGMENT_SEC * sr / hop_length)
n_segments = n_frames // frames_per_segment

def normalize(arr, low, high):
    return np.clip((arr - low) / (high - low), 0, 1)

# 大调/小调模板
major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])

energy_curve = []
valence_curve = []
arousal_curve = []
segment_times = []
segment_rms_means = []
segment_centroid_means = []

for i in range(n_segments):
    start_frame = i * frames_per_segment
    end_frame = start_frame + frames_per_segment

    seg_t = (start_frame + frames_per_segment / 2) * hop_length / sr
    segment_times.append(seg_t)

    # 段内特征均值
    rms_seg = np.mean(rms[start_frame:end_frame])
    centroid_seg = np.mean(centroid[start_frame:end_frame])
    zcr_seg = np.mean(zcr[start_frame:end_frame])
    mfcc_seg = np.mean(mfcc[:, start_frame:end_frame], axis=1)
    chroma_seg = np.mean(chroma[:, start_frame:end_frame], axis=1)
    contrast_seg = np.mean(contrast[:, start_frame:end_frame], axis=1)

    # 段内频谱通量
    if end_frame < spec.shape[1]:
        seg_spec = spec[:, start_frame:end_frame]
        flux_seg = np.mean(np.diff(seg_spec, axis=1) ** 2)
    else:
        flux_seg = 0

    # RMS 方差（段内动态）
    rms_var_seg = np.var(rms[start_frame:end_frame])

    segment_rms_means.append(rms_seg)
    segment_centroid_means.append(centroid_seg)

    # --- 能量得分 ---
    rms_score = normalize(rms_seg, 0.01, 0.3)
    cent_score = normalize(centroid_seg, 300, 4500)
    zcr_score = normalize(zcr_seg, 0.02, 0.18)
    flux_score = normalize(flux_seg, 0, 15)

    e = (rms_score * 0.35 + cent_score * 0.25 + zcr_score * 0.20 + flux_score * 0.15
         + normalize(tempo_global, 60, 180) * 0.05)
    energy_curve.append(e)

    # --- 效价得分 ---
    major_corr = np.corrcoef(chroma_seg, major_profile)[0, 1]
    minor_corr = np.corrcoef(chroma_seg, minor_profile)[0, 1]
    mode_score = normalize(major_corr - minor_corr, -0.5, 0.5)
    mfcc2_score = normalize(mfcc_seg[1], -200, 200)
    contrast_score = normalize(contrast_seg[2], 10, 30)

    v = mode_score * 0.40 + mfcc2_score * 0.35 + contrast_score * 0.25
    valence_curve.append(v)

    # --- 唤醒度得分 ---
    rms_var_score = normalize(rms_var_seg, 0.0, 0.008)
    flux_a_score = normalize(flux_seg, 0, 10)

    a = e * 0.40 + rms_var_score * 0.30 + flux_a_score * 0.30
    arousal_curve.append(a)

energy_curve = np.array(energy_curve)
valence_curve = np.array(valence_curve)
arousal_curve = np.array(arousal_curve)
segment_times = np.array(segment_times)

# ============================================================
# 4. 生成时间曲线图表
# ============================================================
print("\n[4/4] 正在生成时间曲线图表...")

# 发现段落结构：基于能量突变的"副歌检测"
energy_diff = np.diff(energy_curve, prepend=energy_curve[0])
# 能量局部高点 = 可能的副歌
threshold = np.percentile(energy_curve, 70)
chorus_mask = energy_curve > threshold

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle(f"《DREAM-GIRLS》— Camila Cabello  能量与情绪时间曲线  (BPM: {tempo_global:.0f})",
             fontsize=16, fontweight="bold")

# ---- (a) 能量曲线 ----
ax = axes[0, 0]
ax.fill_between(segment_times, energy_curve, alpha=0.15, color="crimson")
ax.plot(segment_times, energy_curve, color="crimson", linewidth=2, label="能量得分")
ax.axhline(np.mean(energy_curve), color="darkred", linestyle="--", linewidth=1,
           alpha=0.6, label=f"均值: {np.mean(energy_curve):.2f}")

# 标记能量高峰（副歌候选）
peak_times = segment_times[chorus_mask]
peak_energies = energy_curve[chorus_mask]
ax.scatter(peak_times, peak_energies, c="darkred", s=20, alpha=0.5, zorder=5,
           label=f"高能段落 (>{threshold:.2f})")

ax.set_title("能量曲线 (Energy Over Time)", fontsize=13, fontweight="bold")
ax.set_xlabel("时间")
ax.set_ylabel("能量得分 (0-1)")
set_time_axis(ax, duration)
ax.set_ylim(0, 1.05)
ax.legend(loc="upper right", fontsize=8)
ax.grid(True, alpha=0.3)

# --- 在x轴上标注段落结构 ---
# 找到连续的chorus区间
edges = np.diff(np.concatenate([[False], chorus_mask, [False]]).astype(int))
starts = np.where(edges == 1)[0]
ends = np.where(edges == -1)[0]
for s_idx, e_idx in zip(starts, ends):
    t_s = segment_times[s_idx]
    t_e = segment_times[min(e_idx, len(segment_times) - 1)]
    if t_e - t_s > 5:  # 只标注 >5秒的段落
        ax.axvspan(t_s, t_e, alpha=0.08, color="orange")
        mid = (t_s + t_e) / 2
        ax.annotate("高能段", (mid, 0.98), ha="center", fontsize=7, color="darkorange",
                    alpha=0.8)

# ---- (b) 效价与唤醒度曲线 ----
ax = axes[0, 1]
ax.plot(segment_times, valence_curve, color="steelblue", linewidth=2, label="效价 (Valence)")
ax.plot(segment_times, arousal_curve, color="darkorange", linewidth=2, label="唤醒度 (Arousal)")
ax.axhline(0.5, color="gray", linestyle=":", alpha=0.5)
ax.axhline(np.mean(valence_curve), color="steelblue", linestyle="--", linewidth=1, alpha=0.5,
           label=f"效价均值: {np.mean(valence_curve):.2f}")
ax.axhline(np.mean(arousal_curve), color="darkorange", linestyle="--", linewidth=1, alpha=0.5,
           label=f"唤醒度均值: {np.mean(arousal_curve):.2f}")
ax.fill_between(segment_times, valence_curve, alpha=0.08, color="steelblue")
ax.fill_between(segment_times, arousal_curve, alpha=0.08, color="darkorange")

ax.set_title("情绪曲线 (Mood Over Time)", fontsize=13, fontweight="bold")
ax.set_xlabel("时间")
ax.set_ylabel("得分 (0-1)")
set_time_axis(ax, duration)
ax.set_ylim(0, 1.05)
ax.legend(loc="upper right", fontsize=8)
ax.grid(True, alpha=0.3)

# ---- (c) 情绪轨迹散点图（效价 × 唤醒度 随时间的轨迹）----
ax = axes[1, 0]
# 用颜色表示时间先后
sc = ax.scatter(arousal_curve, valence_curve, c=segment_times, cmap="viridis",
                s=30, alpha=0.7, edgecolors="white", linewidth=0.3)
# 连线表示时间顺序
for i in range(0, len(arousal_curve) - 1, max(1, len(arousal_curve) // 80)):
    ax.plot(arousal_curve[i:i+2], valence_curve[i:i+2], color="gray",
            alpha=0.2, linewidth=0.5)

# 起点和终点
ax.scatter(arousal_curve[0], valence_curve[0], s=150, c="green", edgecolors="black",
           linewidth=1.5, zorder=10, label="开始")
ax.scatter(arousal_curve[-1], valence_curve[-1], s=150, c="red", edgecolors="black",
           linewidth=1.5, zorder=10, label="结束")

# 象限线
ax.axhline(0.5, color="gray", linestyle="--", alpha=0.4)
ax.axvline(0.5, color="gray", linestyle="--", alpha=0.4)

# 象限标签
ax.text(0.8, 0.8, "兴奋/欢快", ha="center", fontsize=9, color="green", fontweight="bold", alpha=0.7)
ax.text(0.2, 0.8, "紧张/愤怒", ha="center", fontsize=9, color="red", fontweight="bold", alpha=0.7)
ax.text(0.8, 0.2, "轻松/愉悦", ha="center", fontsize=9, color="blue", fontweight="bold", alpha=0.7)
ax.text(0.2, 0.2, "悲伤/忧郁", ha="center", fontsize=9, color="purple", fontweight="bold", alpha=0.7)

cbar = plt.colorbar(sc, ax=ax, shrink=0.8)
cbar.set_label("时间", fontsize=9)

ax.set_title("情绪轨迹 (Valence × Arousal 散点图)", fontsize=13, fontweight="bold")
ax.set_xlabel("唤醒度 (Arousal)")
ax.set_ylabel("效价 (Valence)")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.legend(loc="lower left", fontsize=7)
ax.grid(True, alpha=0.2)

# ---- (d) 综合仪表盘 ----
ax = axes[1, 1]

# RGB 颜色映射：效价 -> 红/绿, 唤醒度 -> 蓝
def mood_to_color(valence, arousal):
    """效价→绿/红，唤醒度→明暗"""
    r = (1 - valence) * 0.9
    g = valence * 0.7
    b = arousal * 0.5
    return (r, g, b)

colors = [mood_to_color(v, a) for v, a in zip(valence_curve, arousal_curve)]

# 绘制带颜色的能量填充曲线
for i in range(len(segment_times) - 1):
    ax.fill_between(segment_times[i:i+2], 0, energy_curve[i:i+2],
                     color=colors[i], alpha=0.7, linewidth=0)

ax.plot(segment_times, energy_curve, color="black", linewidth=1.5, alpha=0.8)

# 叠加平滑趋势线
from scipy.ndimage import uniform_filter1d
window = max(3, len(energy_curve) // 40)
energy_smooth = uniform_filter1d(energy_curve, size=window)
valence_smooth = uniform_filter1d(valence_curve, size=window)
arousal_smooth = uniform_filter1d(arousal_curve, size=window)
ax.plot(segment_times, energy_smooth, color="white", linewidth=2.5, alpha=0.6)
ax.plot(segment_times, energy_smooth, color="black", linewidth=1.5, alpha=0.8,
        label=f"能量趋势 (窗={window})")

ax.set_title("综合能量曲线 (颜色=情绪)", fontsize=13, fontweight="bold")
ax.set_xlabel("时间")
ax.set_ylabel("能量得分 (0-1)")
set_time_axis(ax, duration)
ax.set_ylim(0, 1.05)

# 颜色图例
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=mood_to_color(0.8, 0.8), label="高唤醒 + 高效价"),
    Patch(facecolor=mood_to_color(0.2, 0.8), label="高唤醒 + 低效价"),
    Patch(facecolor=mood_to_color(0.8, 0.2), label="低唤醒 + 高效价"),
    Patch(facecolor=mood_to_color(0.2, 0.2), label="低唤醒 + 低效价"),
]
ax.legend(handles=legend_elements + [plt.Line2D([0], [0], color="black", linewidth=1.5,
                                                 label="能量趋势")],
          loc="upper right", fontsize=7)
ax.grid(True, alpha=0.3)

plt.tight_layout()
fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ============================================================
# 打印统计摘要
# ============================================================
# 歌曲结构分析
energy_diff_smooth = np.diff(energy_smooth)
# 找上升沿和下降沿
rises = np.where(energy_diff_smooth > 0.02)[0]
falls = np.where(energy_diff_smooth < -0.02)[0]
n_builds = len(np.where(np.diff(rises) > 1)[0]) + (1 if len(rises) > 0 else 0)
n_drops = len(np.where(np.diff(falls) > 1)[0]) + (1 if len(falls) > 0 else 0)

print(f"""
{'=' * 60}
  时间曲线分析结果
{'=' * 60}
  歌曲时长: {duration:.0f} 秒 ({duration/60:.1f} 分钟)
  分析分段: {n_segments} 段 (每段 {SEGMENT_SEC} 秒)

  ─── 能量曲线 ───
  能量均值:   {np.mean(energy_curve):.3f}
  能量标准差:  {np.std(energy_curve):.3f}
  能量最大值:  {np.max(energy_curve):.3f} (at {fmt_mmss(segment_times[np.argmax(energy_curve)])})
  能量最小值:  {np.min(energy_curve):.3f} (at {fmt_mmss(segment_times[np.argmin(energy_curve)])})
  高能段落数:  {len(starts)} 处 ({np.sum(chorus_mask) * SEGMENT_SEC:.0f}s, {np.sum(chorus_mask)/len(chorus_mask)*100:.0f}%)

  ─── 情绪曲线 ───
  效价均值:   {np.mean(valence_curve):.3f}
  效价标准差:  {np.std(valence_curve):.3f}
  唤醒度均值:  {np.mean(arousal_curve):.3f}
  唤醒度标准差: {np.std(arousal_curve):.3f}

  ─── 歌曲结构 ───
  能量攀升次数: ~{n_builds} 处（副歌前的铺垫）
  能量骤降次数: ~{n_drops} 处（副歌结束后的过渡）

  情绪走势: {"前高后低" if valence_curve[0] > valence_curve[-1] + 0.05 else
             "前低后高" if valence_curve[-1] > valence_curve[0] + 0.05 else
             "相对平稳"}

  图表已保存至: {OUTPUT_PATH}
{'=' * 60}
""")
