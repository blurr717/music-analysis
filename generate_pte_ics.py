"""
PTE 20天刷题计划 → iOS 日历 .ics 生成器
生成符合 RFC 5545 标准的日历文件，可通过 URL 在 iOS 日历中订阅
"""

from datetime import datetime, timedelta
import uuid

# ============================================================
# 配置
# ============================================================
DAY1_DATE = datetime(2026, 6, 9)   # Day 1
EXAM_DATE = datetime(2026, 6, 30)  # 考试日
TIMEZONE = "Asia/Shanghai"
OUTPUT_FILE = "pte_20day_plan.ics"

# 每日刷题配额 [WFD, SST, SWT, WE]
# 索引 0 = Day 1
PLAN = [
    # Day 1-7 (WFD 一刷)
    [25,  3,  3,  0],   # Day 1
    [28,  4,  4,  1],   # Day 2
    [28,  4,  5,  1],   # Day 3
    [28,  5,  5,  1],   # Day 4
    [30,  5,  5,  2],   # Day 5
    [30,  5,  5,  2],   # Day 6
    [26,  3,  3,  1],   # Day 7  🧪 模考①
    # Day 8-14 (WFD 二刷)
    [30,  5,  5,  2],   # Day 8  🎉 WFD一刷完成
    [28,  5,  5,  1],   # Day 9
    [28,  5,  5,  2],   # Day 10
    [28,  5,  5,  1],   # Day 11
    [28,  5,  5,  1],   # Day 12
    [28,  5,  5,  2],   # Day 13
    [25,  3,  3,  1],   # Day 14 🧪 模考② / 🎉 WFD二刷完成
    # Day 15-19 (WFD 三刷)
    [35,  5,  7,  2],   # Day 15 🎉 SST一刷完成
    [40,  8,  5,  1],   # Day 16 🎉 SWT一刷完成
    [40,  8,  0,  2],   # Day 17 SWT错题
    [40,  8,  0,  1],   # Day 18 SWT错题
    [40,  8,  0,  0],   # Day 19 🎉 WFD三刷完成 / SWT错题
    # Day 20
    [0,   0,  0,  0],   # Day 20 考前热身（数量为0表示灵活安排）
]

# 特殊标记
MOCK_DAYS = {7: "模考①", 14: "模考②"}
MILESTONES = {
    8:  "🎉 WFD一刷完成 (195/195)",
    14: "🎉 WFD二刷完成 (390/195)",
    15: "🎉 SST一刷完成 (67/67)",
    16: "🎉 SWT一刷完成 (75/75)",
    19: "🎉 WFD三刷完成 (585/195)",
}

# 话题类型（用于Essay）
ESSAY_TOPICS = [
    "教育", "科技", "环境", "健康", "社会", "经济", "文化", "媒体"
]

# ============================================================
# iCalendar 生成
# ============================================================

def escape_ics(text: str) -> str:
    """转义 iCalendar 文本中的特殊字符"""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def format_dt(dt: datetime) -> str:
    """格式化为 iCalendar 本地时间 (带 TZID)"""
    return dt.strftime("%Y%m%dT%H%M%S")


def make_event(dt_start: datetime, dt_end: datetime, summary: str, description: str) -> str:
    """生成单个 VEVENT"""
    uid = str(uuid.uuid4())
    from datetime import timezone as tz
    now_utc = datetime.now(tz.utc).strftime("%Y%m%dT%H%M%SZ")
    return (
        "BEGIN:VEVENT\r\n"
        f"DTSTART;TZID={TIMEZONE}:{format_dt(dt_start)}\r\n"
        f"DTEND;TZID={TIMEZONE}:{format_dt(dt_end)}\r\n"
        f"DTSTAMP:{now_utc}\r\n"
        f"UID:{uid}\r\n"
        f"SUMMARY:{escape_ics(summary)}\r\n"
        f"DESCRIPTION:{escape_ics(description)}\r\n"
        "END:VEVENT\r\n"
    )


def generate_ics() -> str:
    """生成完整的 .ics 文件内容"""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PTE 20-Day Study Plan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:PTE 20天冲刺计划",
        f"X-WR-CALDESC:PTE 目标58分 (WFD195/SST67/SWT75/WE39)",
        f"X-WR-TIMEZONE:{TIMEZONE}",
        # 时区定义
        "BEGIN:VTIMEZONE",
        f"TZID:{TIMEZONE}",
        "BEGIN:STANDARD",
        "DTSTART:19700101T000000",
        "TZOFFSETFROM:+0800",
        "TZOFFSETTO:+0800",
        "TZNAME:CST",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]

    for i, (wfd, sst, swt, we) in enumerate(PLAN):
        day_num = i + 1
        plan_date = DAY1_DATE + timedelta(days=i)
        date_str = plan_date.strftime("%m/%d")
        weekday = ["周一","周二","周三","周四","周五","周六","周日"][plan_date.weekday()]

        day_label = f"Day{day_num} ({date_str} {weekday})"

        milestone = MILESTONES.get(day_num, "")
        mock = MOCK_DAYS.get(day_num, "")

        # ================================================================
        # 模考日 (Day 7, 14)
        # ================================================================
        if mock:
            # 14:00-14:30 热身
            lines.append(make_event(
                plan_date.replace(hour=14, minute=0),
                plan_date.replace(hour=14, minute=30),
                f"🗣 模考热身 RA+RS | {day_label}",
                f"📌 {day_label} - {mock}\n\nRA 3篇（轻度）\nRS 20句\n\n准备进入模考状态"
            ))
            # 14:30-17:30 模考
            lines.append(make_event(
                plan_date.replace(hour=14, minute=30),
                plan_date.replace(hour=17, minute=30),
                f"🧪 {mock} 完整模考 | {day_label}",
                f"📌 {day_label} - 模考日\n\n完整模考 3小时\n猩际/官方模考卷\n模拟真实环境，中间不休息"
            ))
            # 18:30-20:00 模考分析
            lines.append(make_event(
                plan_date.replace(hour=18, minute=30),
                plan_date.replace(hour=20, minute=0),
                f"📊 模考逐题分析 | {day_label}",
                f"📌 {day_label}\n\n逐题分析模考结果\n记录每模块得分和失分原因"
            ))
            # 21:00-22:30 弱项练习 + DI/FIB
            lines.append(make_event(
                plan_date.replace(hour=21, minute=0),
                plan_date.replace(hour=22, minute=30),
                f"🔧 弱项突破 + DI/FIB | {day_label}",
                f"📌 {day_label}\n\n根据模考结果专项补弱\nDI 5道\nFIB 3篇"
            ))
            # 00:00-02:00 WFD错题重练 (次日凌晨)
            next_date = plan_date + timedelta(days=1)
            lines.append(make_event(
                next_date.replace(hour=0, minute=0),
                next_date.replace(hour=2, minute=0),
                f"📝 WFD错题重练 | {day_label}",
                f"📌 {day_label}\n\nWFD {wfd}题（错题优先）\nSST {sst}题"
            ))
            # 02:00-03:00 复盘 (次日凌晨)
            lines.append(make_event(
                next_date.replace(hour=2, minute=0),
                next_date.replace(hour=3, minute=0),
                f"📋 错题复盘 | {day_label}",
                f"📌 {day_label}\n\n当日错题复习\nWFD错句重练\n生词回顾"
            ))
            continue

        # ================================================================
        # Day 20 — 考前最后一天
        # ================================================================
        if day_num == 20:
            lines.append(make_event(
                plan_date.replace(hour=14, minute=0),
                plan_date.replace(hour=15, minute=30),
                f"🗣 考前热身 RA+RS | {day_label}",
                f"📌 {day_label} - 考前最后一天\n\nRA 3篇（轻度热身）\nRS 20句\n\n保持语感，不过度疲劳"
            ))
            lines.append(make_event(
                plan_date.replace(hour=15, minute=30),
                plan_date.replace(hour=17, minute=0),
                f"📝 WFD易错句最后过一遍 | {day_label}",
                f"📌 {day_label}\n\nWFD 高频易错句最后一遍\nSST关键词快速浏览"
            ))
            lines.append(make_event(
                plan_date.replace(hour=19, minute=0),
                plan_date.replace(hour=20, minute=30),
                f"📋 模板默写 + 错题浏览 | {day_label}",
                f"📌 {day_label}\n\n全部模板默写一遍 (DI/RL/SWT/SST/Essay)\n浏览错题本\nEssay话题论点快速回顾"
            ))
            lines.append(make_event(
                plan_date.replace(hour=21, minute=0),
                plan_date.replace(hour=22, minute=0),
                f"😴 收拾 + 早睡 | {day_label}",
                f"📌 {day_label}\n\n收拾考试用品\n22:00前睡觉\n保证充足睡眠！"
            ))
            continue

        # ================================================================
        # 普通日 — 统一6时段，结束于次日03:00
        # ================================================================

        milestone_note = f"\n{milestone}" if milestone else ""
        wfd_round = "一刷" if day_num <= 7 else ("二刷" if day_num <= 14 else "三刷")
        wfd_progress = sum(p[0] for p in PLAN[:day_num])

        # ---- ① 14:00-15:30 RA + RS ----
        lines.append(make_event(
            plan_date.replace(hour=14, minute=0),
            plan_date.replace(hour=15, minute=30),
            f"🗣 RA 5篇 + RS 50句 | {day_label}",
            f"📌 {day_label}{milestone_note}\n\nRA (Read Aloud) 5篇\n  · 录音对比，纠正发音和流利度\n  · 注意意群划分、重弱读\n\nRS (Repeat Sentence) 50句\n  · 抓主干（主+谓+宾）\n  · 模仿语调和重音\n\n🎯 目标：暖口醒脑，进入英语状态"
        ))

        # ---- ② 15:30-18:00 WFD + SWT ----
        swt_label = f"SWT {swt}题" if swt > 0 else "SWT 错题回顾"
        lines.append(make_event(
            plan_date.replace(hour=15, minute=30),
            plan_date.replace(hour=18, minute=0),
            f"📝 WFD {wfd}题 + {swt_label} | {day_label}",
            f"📌 {day_label}\n\nWFD (Write From Dictation) {wfd}题 ({wfd_round})\n  · 首字母法记笔记\n  · 注意拼写和单复数\n  · 累计进度: {wfd_progress}/195\n\nSWT (Summarize Written Text) {swt_label}\n  · 模板：用 and/; 连接主题句\n  · 限时10分钟/篇"
        ))

        # 18:00-19:00 晚餐休息（不生成事件）

        # ---- ③ 19:00-21:00 SST + WE ----
        we_desc = ""
        if we > 0:
            topic_idx = (day_num - 1) % len(ESSAY_TOPICS)
            we_desc = f"\nWE Essay {we}篇（话题: {ESSAY_TOPICS[topic_idx]}）\n  · 套用万能模板\n  · 计时18-20分钟/篇\n  · 留2分钟检查拼写"
        else:
            we_desc = "\nWE 模板复习/论点积累\n  · 默写Essay模板\n  · 浏览话题论点素材"

        sst_round = " (二刷重点篇)" if day_num >= 15 else ""
        lines.append(make_event(
            plan_date.replace(hour=19, minute=0),
            plan_date.replace(hour=21, minute=0),
            f"🎧 SST {sst}题 + WE {we}篇 | {day_label}",
            f"📌 {day_label}\n\nSST (Summarize Spoken Text) {sst}题{sst_round}\n  · 听2遍写总结\n  · 模板+关键词提取\n  · 注意语法和拼写{we_desc}"
        ))

        # ---- ④ 21:30-23:00 DI + FIB ----
        lines.append(make_event(
            plan_date.replace(hour=21, minute=30),
            plan_date.replace(hour=23, minute=0),
            f"📖 DI 10道 + FIB 5篇 | {day_label}",
            f"📌 {day_label}\n\nDI (Describe Image) 10道\n  · 模板计时（25s准备+35s说）\n  · 柱/线/饼/流程/地图各2道\n\nFIB (Fill in Blanks) 5篇\n  · FIB-RW 3篇 + FIB-R 2篇\n  · 注意固定搭配和语法\n  · 积累生词和搭配"
        ))

        # 23:00-00:00 休息（不生成事件）

        # 次日凌晨日期
        next_date = plan_date + timedelta(days=1)

        # ---- ⑤ 00:00-02:00 WFD错题 + 阅读 ----
        reading_task = "RO 10题 + FIB-RW 8题" if day_num % 2 == 0 else "FIB-R 8题 + RO 10题"
        lines.append(make_event(
            next_date.replace(hour=0, minute=0),
            next_date.replace(hour=2, minute=0),
            f"📝 WFD错题重练 + 阅读 | {day_label}",
            f"📌 {day_label}\n\nWFD 错题重练\n  · 重做当日+历史错题\n  · 每句练到全对\n\n阅读专项 {reading_task}\n  · RO: 找首句+逻辑对\n  · FIB: 上下文推理+语法判断"
        ))

        # ---- ⑥ 02:00-03:00 复盘收尾 ----
        lines.append(make_event(
            next_date.replace(hour=2, minute=0),
            next_date.replace(hour=3, minute=0),
            f"📋 错题复盘 + 生词复习 | {day_label}",
            f"📌 {day_label}\n\nWFD 今日错句最终过一遍\n生词 + 固定搭配复习\n当日学习记录\n\n📊 今日完成:\n  WFD {wfd}题 | SST {sst}题 | SWT {swt_label}\n  WE {we}篇 | RA 5篇 | RS 50句 | DI 10道 | FIB 5篇\n\n💪 明天继续！"
        ))

    # ---- 考试日 6月30日 ----
    exam_dt = EXAM_DATE
    lines.append(make_event(
        exam_dt.replace(hour=7, minute=30),
        exam_dt.replace(hour=8, minute=0),
        "🎧 考前热耳",
        "听10分钟英语新闻/播客\n让耳朵进入英语状态"
    ))
    lines.append(make_event(
        exam_dt.replace(hour=8, minute=0),
        exam_dt.replace(hour=8, minute=30),
        "🗣 考前热身",
        "RA 3篇（轻微热身）\nRS 20句\n默念所有模板"
    ))
    lines.append(make_event(
        exam_dt.replace(hour=9, minute=0),
        exam_dt.replace(hour=12, minute=0),
        "🎯 PTE 考试！",
        "目标：四个58！\n\n考试中：\n① 不纠结已过去的题\n② 写作留2分钟查拼写\n③ WFD仔细听，首字母记\n④ 保持节奏，相信自己的准备！\n\n💪 你已经刷了585道WFD，67篇SST，75篇SWT\n你可以的！"
    ))
    lines.append(make_event(
        exam_dt.replace(hour=12, minute=0),
        exam_dt.replace(hour=13, minute=0),
        "🎉 解放！",
        "无论结果如何，你已经尽力了！\n好好吃一顿，放松一下 🎉"
    ))

    # 6月29日 缓冲日
    buffer_date = EXAM_DATE - timedelta(days=1)
    lines.append(make_event(
        buffer_date.replace(hour=14, minute=0),
        buffer_date.replace(hour=15, minute=30),
        "🗣 RA 3篇 + RS 20句 | 考前缓冲",
        "📌 考前缓冲日\n\nRA 3篇（轻度）\nRS 20句\n\n保持语感，不过度疲劳"
    ))
    lines.append(make_event(
        buffer_date.replace(hour=15, minute=30),
        buffer_date.replace(hour=18, minute=0),
        "📝 WFD易错句 + SST关键词 | 考前缓冲",
        "📌 考前缓冲日\n\nWFD 高频易错句最后过一遍\nSST 67篇关键词快速浏览\nSWT 错题回顾"
    ))
    lines.append(make_event(
        buffer_date.replace(hour=19, minute=0),
        buffer_date.replace(hour=21, minute=0),
        "📋 模板默写 + 错题浏览 | 考前缓冲",
        "📌 考前缓冲日\n\n全部模板默写一遍\n浏览错题本\nEssay话题论点快速回顾"
    ))
    lines.append(make_event(
        buffer_date.replace(hour=21, minute=30),
        buffer_date.replace(hour=22, minute=0),
        "😴 收拾 + 早睡 | 考前缓冲",
        "📌 考前缓冲日\n\n收拾考试用品\n深呼吸，放轻松\n22:00前睡觉！"
    ))

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    ics_content = generate_ics()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(ics_content)

    # 统计
    event_count = ics_content.count("BEGIN:VEVENT")
    total_wfd = sum(p[0] for p in PLAN)
    total_sst = sum(p[1] for p in PLAN[:15])  # 一刷67全覆盖

    print(f"✅ 已生成: {OUTPUT_FILE}")
    print(f"📅 事件总数: {event_count}")
    print(f"📊 WFD 总量: {total_wfd} 题 (目标585)")
    print(f"📊 SST 一刷: 67 题 (Day1-15)")
    print(f"📅 Day1: {DAY1_DATE.strftime('%Y-%m-%d')} → Day20: {(DAY1_DATE + timedelta(days=19)).strftime('%Y-%m-%d')}")
    print(f"🎯 考试日: {EXAM_DATE.strftime('%Y-%m-%d')}")
    print(f"\n📱 iOS 订阅 URL (push 后可用):")
    print(f"   https://raw.githubusercontent.com/blurr717/music-analysis/master/{OUTPUT_FILE}")
