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
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
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

        # 里程碑
        milestone = MILESTONES.get(day_num, "")
        # 模考
        mock = MOCK_DAYS.get(day_num, "")

        # ---- 事件1: 口语热身 14:00-15:00 ----
        t1_start = plan_date.replace(hour=14, minute=0)
        t1_end = plan_date.replace(hour=15, minute=0)
        summary1 = f"🗣 口语热身 RA+RS | {day_label}"
        desc1 = f"📌 {day_label}"
        if milestone:
            desc1 += f"\n{milestone}"
        desc1 += "\n\nRA (Read Aloud) 5-8篇\nRS (Repeat Sentence) 30-50句\n\n🎯 目标：暖口醒脑，进入英语状态"
        lines.append(make_event(t1_start, t1_end, summary1, desc1))

        # ---- 事件2: WFD + SWT 15:00-17:30 ----
        t2_start = plan_date.replace(hour=15, minute=0)
        t2_end = plan_date.replace(hour=17, minute=30)

        if mock:
            summary2 = f"🧪 {mock} 模考 | {day_label}"
            desc2 = f"📌 {day_label} - 模考日\n\n完整模考 3小时 (猩际/官方模考卷)\n模拟真实考试环境，中间不休息"
            # 模考占用更长时间
            t2_end = plan_date.replace(hour=18, minute=0)
        elif day_num == 20:
            summary2 = f"🔥 考前最后热身 | {day_label}"
            desc2 = f"📌 {day_label} - 考前最后一天\n\nRA 3篇（轻度热身）\nRS 20句\n默念所有模板（DI/RL/SWT/SST/Essay）\n\n⚠️ 22:00前睡觉！"
        else:
            swt_label = f"SWT {swt}题" if swt > 0 else "SWT 错题回顾"
            wfd_round = ""
            if day_num <= 7:
                wfd_round = " (一刷)"
            elif day_num <= 14:
                wfd_round = " (二刷)"
            else:
                wfd_round = " (三刷)"

            summary2 = f"📝 WFD {wfd}题 + {swt_label} | {day_label}"
            desc2 = f"📌 {day_label}"
            if milestone:
                desc2 += f"\n{milestone}"
            desc2 += f"\n\nWFD (Write From Dictation) {wfd}题{wfd_round}\nSWT (Summarize Written Text) {swt_label}\n\n总进度: WFD {sum(p[0] for p in PLAN[:day_num])}/195{' ✓一刷' if day_num >= 8 else ''}"

        lines.append(make_event(t2_start, t2_end, summary2, desc2))

        # 模考日简化后续事件
        if mock:
            # 模考后：分析 + 轻量复习
            t3_start = plan_date.replace(hour=18, minute=30)
            t3_end = plan_date.replace(hour=20, minute=0)
            summary3 = f"📊 模考分析 | {day_label}"
            desc3 = f"📌 {day_label}\n\n逐题分析模考结果\n记录每模块得分和失分原因\n\nWFD {wfd}题 + SST {sst}题"
            lines.append(make_event(t3_start, t3_end, summary3, desc3))

            t4_start = plan_date.replace(hour=20, minute=30)
            t4_end = plan_date.replace(hour=22, minute=0)
            lines.append(make_event(t4_start, t4_end,
                f"📖 阅读 + 模板保温 | {day_label}",
                f"📌 {day_label}\n\nFIB-RW 8题 + RO 5题\nDI/RL 模板练习各3题\n错题复盘"))

            t5_start = plan_date.replace(hour=22, minute=0)
            t5_end = plan_date.replace(hour=22, minute=30)
            lines.append(make_event(t5_start, t5_end,
                f"📋 错题复盘 | {day_label}",
                f"📌 {day_label}\n\n当日错题复习\nWFD错句重练\n生词回顾"))

            continue

        # Day 20 简化
        if day_num == 20:
            t3_start = plan_date.replace(hour=18, minute=0)
            t3_end = plan_date.replace(hour=19, minute=30)
            lines.append(make_event(t3_start, t3_end,
                f"📋 错题浏览 + 模板默写 | {day_label}",
                f"📌 {day_label}\n\n浏览所有错题本\n全部模板默写一遍\nEssay话题论点快速回顾"))

            t4_start = plan_date.replace(hour=21, minute=0)
            t4_end = plan_date.replace(hour=21, minute=30)
            lines.append(make_event(t4_start, t4_end,
                f"😴 早睡 | {day_label}",
                f"📌 {day_label}\n\n收拾考试用品\n22:00前睡觉\n保证充足睡眠"))
            continue

        # ---- 事件3: SST + WE 18:00-20:00 ----
        t3_start = plan_date.replace(hour=18, minute=0)
        t3_end = plan_date.replace(hour=20, minute=0)

        we_label = ""
        if we > 0:
            topic_idx = (day_num - 1) % len(ESSAY_TOPICS)
            we_label = f"\nWE Essay {we}篇（话题: {ESSAY_TOPICS[topic_idx]}）"
        else:
            we_label = "\nWE 模板复习/论点积累"

        sst_round = " (二刷重点篇)" if day_num >= 15 else ""

        summary3 = f"🎧 SST {sst}题 + WE {we}篇 | {day_label}"
        desc3 = f"📌 {day_label}\n\nSST (Summarize Spoken Text) {sst}题{sst_round}{we_label}"

        lines.append(make_event(t3_start, t3_end, summary3, desc3))

        # ---- 事件4: 阅读 + DI/RL 20:30-22:00 ----
        t4_start = plan_date.replace(hour=20, minute=30)
        t4_end = plan_date.replace(hour=22, minute=0)

        reading_items = ""
        if day_num % 2 == 0:
            reading_items = "FIB-RW 10题 + RO 8题"
        else:
            reading_items = "FIB-R 8题 + RO 10题"

        summary4 = f"📖 阅读 + DI/RL | {day_label}"
        desc4 = f"📌 {day_label}\n\n{reading_items}\nDI (Describe Image) 5题（模板计时）\nRL (Retell Lecture) 3题"

        lines.append(make_event(t4_start, t4_end, summary4, desc4))

        # ---- 事件5: 错题复盘 22:00-22:30 ----
        t5_start = plan_date.replace(hour=22, minute=0)
        t5_end = plan_date.replace(hour=22, minute=30)

        summary5 = f"📋 错题复盘 | {day_label}"
        desc5 = f"📌 {day_label}\n\nWFD 当日错句重练\n生词 + 固定搭配复习\n当日学习记录"

        lines.append(make_event(t5_start, t5_end, summary5, desc5))

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
        buffer_date.replace(hour=18, minute=0),
        "🔋 考前缓冲日 - 自由复习",
        "考前最后一天自由安排\n\n建议：\n- WFD易错句最后过一遍\n- 模板默写\n- 轻松复习，不过度疲劳\n- 晚上10点前睡觉"
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
