from matplotlib.dates import date2num
from ..data_manager import data_manager

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    Event,
    PrivateMessageEvent,
    GroupMessageEvent,
    MessageSegment,
)
from sklearn.linear_model import LinearRegression
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import io

plt.rcParams["font.sans-serif"] = ["Noto Sans Mono CJK SC"]  # 用来正常显示中文标签
plt.rcParams["axes.unicode_minus"] = False  # 用来正常显示负号

graph_command = on_command("图表", rule=to_me())


@graph_command.handle()
async def handle_test(event: Event):
    if isinstance(event, PrivateMessageEvent):
        prefix = "user"
        id = event.get_user_id()
    elif isinstance(event, GroupMessageEvent):
        prefix = "group"
        id = str(event.group_id)

    if not id in data_manager.binding_data[prefix]:
        await graph_command.finish("未检测到绑定信息，请先绑定宿舍")
        return

    campus, building_name, room_id = data_manager.binding_data[prefix][id]
    location = f"{campus}-{building_name}-{room_id}"
    records = data_manager.electricity_data[location]

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

    plt.figure(figsize=(12, 8))

    for idx, (segment, color) in enumerate(zip(segments, colors)):
        seg_times = [datetime.fromisoformat(record[0]) for record in segment]
        seg_values = [record[1] for record in segment]

        time_stamps = np.array([t.timestamp() for t in seg_times]).reshape(-1, 1)
        values_array = np.array(seg_values).reshape(-1, 1)

        if len(seg_times) > 1:
            model = LinearRegression()
            model.fit(time_stamps, values_array)

            m = model.coef_[0][0]
            b = model.intercept_[0]

            ref_time_num = date2num(seg_times[0])
            ref_value = seg_values[0]
            slope_per_day = m * 86400

            plt.axline(
                (ref_time_num, ref_value),
                slope=slope_per_day,
                linestyle="--",
                color=color,
                label=f"Segment {idx + 1} (Fit)",
            )

            duration_hours = (
                time_stamps[-1, 0] - time_stamps[0, 0]
            ) / 3600  # 持续时间（小时）
            energy_used = seg_values[0] - seg_values[-1]  # 消耗的电量（度）
            avg_power_kWh = (
                energy_used / duration_hours if duration_hours > 0 else 0
            )  # 平均功率（度/小时）
            avg_power_W = avg_power_kWh * 1000  # 平均功率（瓦特）

            # 标注平均功率（度/小时 和 瓦特）
            mid_time = seg_times[len(seg_times) // 2]
            mid_value = np.mean(seg_values)
            label = f"{avg_power_kWh:.2f} 度/小时\n({avg_power_W:.2f} W)"
            plt.text(mid_time, mid_value, label, color=color, fontsize=18, ha="center")

            if m != 0:
                y0_crossing_time_ts = -b / m
                y0_crossing_time = datetime.fromtimestamp(y0_crossing_time_ts)

                plt.scatter([y0_crossing_time], [0], color=color, zorder=5)
                plt.text(
                    y0_crossing_time,
                    0,
                    y0_crossing_time.strftime("%Y-%m-%d %H:%M:%S"),
                    color=color,
                    fontsize=9,
                    ha="center",
                    va="bottom",
                )

        plt.scatter(seg_times, seg_values, label=f"Segment {idx + 1}", color=color)

    plt.title(f"电量变化与拟合 - {location}", fontsize=16)
    plt.xlabel("时间", fontsize=12)
    plt.ylabel("电量 (度)", fontsize=12)
    plt.ylim(bottom=0)
    # plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    img_bytes_io = io.BytesIO()
    plt.savefig(img_bytes_io, format="png")

    await graph_command.finish(MessageSegment.image(img_bytes_io))
