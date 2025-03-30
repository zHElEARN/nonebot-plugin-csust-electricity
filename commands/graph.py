import io
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter, DayLocator, date2num
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, MessageSegment
from nonebot.exception import FinishedException
from nonebot.rule import to_me
from sklearn.linear_model import LinearRegression

from ..db.electricity_db import ElectricityHistory, SessionLocal
from ..utils.common import get_binding, get_sender_info

plt.rcParams["font.sans-serif"] = ["Noto Sans Mono CJK SC"]  # 用来正常显示中文标签
plt.rcParams["axes.unicode_minus"] = False  # 用来正常显示负号
# 添加以下设置确保不会在任务栏中显示窗口
plt.switch_backend("Agg")

graph_command = on_command("图表", rule=to_me())


@graph_command.handle()
async def handle_graph(event: Event):
    try:
        # 使用utils.common中的函数获取发送者信息
        sender_type, sender_id = get_sender_info(event)

        # 使用utils.common中的函数获取绑定信息
        binding = get_binding(sender_type, sender_id)

        if not binding:
            await graph_command.finish("未检测到绑定信息，请先绑定宿舍")
            return

        # 创建数据库会话
        session = SessionLocal()
        try:
            # 查询电量历史记录
            history_records = (
                session.query(ElectricityHistory)
                .filter(
                    ElectricityHistory.campus == binding.campus,
                    ElectricityHistory.building == binding.building,
                    ElectricityHistory.room == binding.room,
                )
                .order_by(ElectricityHistory.record_time)
                .all()
            )

            if not history_records:
                await graph_command.finish("没有查询到电量记录")
                return

            # 转换记录为时间和电量值列表
            records = [
                (record.record_time, record.electricity) for record in history_records
            ]

            location = f"{binding.campus}-{binding.building}-{binding.room}"

            # 生成图表
            img_bytes_io = generate_graph(records, location)

            await graph_command.finish(MessageSegment.image(img_bytes_io))
        finally:
            session.close()
    except FinishedException:
        pass
    except Exception as e:
        await graph_command.finish(f"生成图表时发生错误: {str(e)}")


def generate_graph(records, location):
    values = [record[1] for record in records]

    segments = []
    current_segment = [records[0]]  # 初始化第一段

    for i in range(1, len(records)):
        if values[i] > values[i - 1]:
            segments.append(current_segment)
            current_segment = [records[i]]
        else:
            current_segment.append(records[i])

    segments.append(current_segment)  # 添加最后一段

    vibrant_cmap = plt.cm.Set1
    num_colors = max(9, len(segments))
    colors = vibrant_cmap(np.linspace(0, 1, num_colors))

    # 创建图表并设置大小
    fig, ax = plt.subplots(figsize=(12, 8))

    # 获取所有记录的日期范围
    all_dates = [record[0] for record in records]
    min_date = min(all_dates)
    max_date = max(all_dates)

    # 对于预测到电量为0的点，可能需要更大的时间范围
    prediction_dates = []

    for idx, (segment, color) in enumerate(zip(segments, colors)):
        seg_times = [record[0] for record in segment]  # 直接使用datetime对象
        seg_values = [record[1] for record in segment]

        time_stamps = np.array([t.timestamp() for t in seg_times]).reshape(-1, 1)
        values_array = np.array(seg_values).reshape(-1, 1)

        if len(seg_times) > 1:
            # 使用线性回归拟合数据
            model = LinearRegression()
            model.fit(time_stamps, values_array)

            m = model.coef_[0][0]
            b = model.intercept_[0]

            ref_time_num = date2num(seg_times[0])
            ref_value = seg_values[0]
            slope_per_day = m * 86400

            ax.axline(
                (ref_time_num, ref_value),
                slope=slope_per_day,
                linestyle="--",
                color=color,
                label=f"段 {idx + 1} (拟合)",
            )

            # 计算功率信息
            duration_hours = (time_stamps[-1, 0] - time_stamps[0, 0]) / 3600
            energy_used = seg_values[0] - seg_values[-1]
            avg_power_kWh = energy_used / duration_hours if duration_hours > 0 else 0
            avg_power_W = avg_power_kWh * 1000

            # 标注平均功率
            mid_time = seg_times[len(seg_times) // 2]
            mid_value = np.mean(seg_values)
            label = f"{avg_power_kWh:.2f} 度/小时\n({avg_power_W:.2f} W)"
            ax.text(mid_time, mid_value, label, color=color, fontsize=12, ha="center")

            # 预测电量耗尽时间点
            if m < 0:
                y0_crossing_time_ts = -b / m
                y0_crossing_time = datetime.fromtimestamp(y0_crossing_time_ts)
                prediction_dates.append(y0_crossing_time)

                # 绘制预测的零点
                ax.scatter(
                    [y0_crossing_time], [0], color=color, zorder=5, s=50, marker="X"
                )
                ax.text(
                    y0_crossing_time,
                    0,
                    f"预计电量耗尽:\n{y0_crossing_time.strftime('%m-%d %H:%M')}",
                    color=color,
                    fontsize=9,
                    ha="center",
                    va="bottom",
                    rotation=45,
                )

        ax.scatter(seg_times, seg_values, label=f"段 {idx + 1}", color=color)

    # 调整x轴的范围以包含预测点
    if prediction_dates:
        max_prediction = max(prediction_dates)
        if max_prediction > max_date:
            max_date = max_prediction

    # 确保图表范围至少包括一周
    date_range = max_date - min_date
    if date_range.days < 7:
        max_date = min_date + timedelta(days=7)

    # 再额外增加两天，确保能看到预测点
    max_date += timedelta(days=2)

    ax.set_xlim(min_date, max_date)

    # 设置每天一个网格
    ax.xaxis.set_major_locator(DayLocator())
    ax.xaxis.set_major_formatter(DateFormatter("%m-%d"))
    ax.grid(True, which="major", axis="both", linestyle="-")

    # 旋转x轴日期标签以避免重叠
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    ax.set_title(f"电量变化与拟合 - {location}", fontsize=16)
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("电量 (度)", fontsize=12)
    ax.set_ylim(bottom=0)
    ax.legend()

    plt.tight_layout()
    img_bytes_io = io.BytesIO()
    plt.savefig(img_bytes_io, format="png", dpi=100)
    img_bytes_io.seek(0)

    plt.close(fig)  # 明确关闭图表释放资源

    return img_bytes_io
