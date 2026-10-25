
import pulp
import streamlit as st

# 设置网页标题和布局
st.set_page_config(page_title="极简数字凑数工具", layout="wide")

st.title("📊 极简数字凑数工具 (Excel 复制即用版)")
st.markdown("---")


# ==================== 核心算法逻辑 ====================
def solve_flexible_subset(numbers, target_1, target_2, target_3=None):
    total_len = len(numbers)
    use_third_target = target_3 is not None

    prob = pulp.LpProblem(
        "Flexible_Subset_Optimization",
        pulp.LpMinimize
    )

    # 第一、第二阶段的选择变量
    y1 = pulp.LpVariable.dicts("y1", range(total_len), cat="Binary")
    y2 = pulp.LpVariable.dicts("y2", range(total_len), cat="Binary")

    # 是否启用第三阶段
    if use_third_target:
        y3 = pulp.LpVariable.dicts("y3", range(total_len), cat="Binary")

    # 第一、第二阶段的偏差变量
    d1_pos = pulp.LpVariable("d1_pos", lowBound=0)
    d1_neg = pulp.LpVariable("d1_neg", lowBound=0)
    d2_pos = pulp.LpVariable("d2_pos", lowBound=0)
    d2_neg = pulp.LpVariable("d2_neg", lowBound=0)

    # 优化目标：尽量减小目标偏差
    objective = d1_pos + d1_neg + d2_pos + d2_neg

    # 第三阶段的偏差变量，仅在启用时创建
    if use_third_target:
        d3_pos = pulp.LpVariable("d3_pos", lowBound=0)
        d3_neg = pulp.LpVariable("d3_neg", lowBound=0)
        objective += d3_pos + d3_neg

    prob += objective

    # 每个数字最多分配到一个阶段
    for i in range(total_len):
        if use_third_target:
            prob += y1[i] + y2[i] + y3[i] <= 1
        else:
            prob += y1[i] + y2[i] <= 1

    # 计算各阶段的数字之和
    sum_part1 = pulp.lpSum(
        numbers[i] * y1[i] for i in range(total_len)
    )
    sum_part2 = pulp.lpSum(
        numbers[i] * y2[i] for i in range(total_len)
    )

    # 第一阶段累计和接近目标值1
    prob += sum_part1 - target_1 == d1_pos - d1_neg

    # 第二阶段累计和接近目标值2
    prob += (
        sum_part1 + sum_part2 - target_2
        == d2_pos - d2_neg
    )

    # 第三阶段：仅在启用第三个目标值时参与计算
    if use_third_target:
        sum_part3 = pulp.lpSum(
            numbers[i] * y3[i] for i in range(total_len)
        )

        prob += (
            sum_part1 + sum_part2 + sum_part3 - target_3
            == d3_pos - d3_neg
        )

    # 求解
    prob.solve(
        pulp.PULP_CBC_CMD(
            msg=False,
            timeLimit=60,
            gapRel=0.001
        )
    )

    # 检查求解状态
    if pulp.LpStatus[prob.status] not in ("Optimal", "Integer Feasible"):
        raise ValueError(f"求解失败，状态：{pulp.LpStatus[prob.status]}")

    # 提取各阶段数字
    part1_list = [
        numbers[i] for i in range(total_len)
        if (pulp.value(y1[i]) or 0) > 0.5
    ]

    part2_list = [
        numbers[i] for i in range(total_len)
        if (pulp.value(y2[i]) or 0) > 0.5
    ]

    if use_third_target:
        part3_list = [
            numbers[i] for i in range(total_len)
            if (pulp.value(y3[i]) or 0) > 0.5
        ]
    else:
        part3_list = []

    # 未分配的数字
    remain_list = [
        numbers[i] for i in range(total_len)
        if (
            (pulp.value(y1[i]) or 0) < 0.5
            and (pulp.value(y2[i]) or 0) < 0.5
            and (
                not use_third_target
                or (pulp.value(y3[i]) or 0) < 0.5
            )
        )
    ]

    return part1_list, part2_list, part3_list, remain_list


# ==================== 界面布局 ====================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📥 输入数据与参数")

    target_1 = st.number_input(
        "第一阶段目标和",
        value=35000.0,
        step=1000.0
    )

    target_2 = st.number_input(
        "第二阶段累计目标和",
        value=50000.0,
        step=1000.0
    )

    # 可选启用第三个目标值
    use_third_target = st.checkbox(
        "启用第三个目标值（划分为四段）",
        value=False
    )

    target_3 = None
    if use_third_target:
        target_3 = st.number_input(
            "第三阶段累计目标和",
            value=70000.0,
            step=1000.0
        )

        if target_3 < target_2:
            st.warning("建议第三阶段目标值不小于第二阶段目标值。")

    default_input = (
        "2761\n2507\n2124\n1860\n2248.5\n"
        "1912.5\n1562\n2059.5"
    )

    user_input = st.text_area(
        "请在此粘贴从 Excel 复制的数字列（每行一个数字）：",
        value=default_input,
        height=400,
    )

    # 解析输入数据
    my_numbers = []
    if user_input:
        lines = user_input.splitlines()
        try:
            my_numbers = [
                float(line.strip())
                for line in lines
                if line.strip()
            ]
        except ValueError:
            st.error("⚠️ 解析失败！请检查是否包含非数字内容。")
            my_numbers = []

    if my_numbers:
        st.caption(
            f"✅ 成功识别 **{len(my_numbers)}** 个数字，"
            f"当前总和为：{sum(my_numbers):,.2f}"
        )


with col_right:
    st.subheader("📤 求解结果（直接复制）")

    if my_numbers:
        if st.button(
            "🚀 开始智能计算",
            type="primary",
            use_container_width=True
        ):
            with st.spinner("计算中..."):
                try:
                    part1, part2, part3, remain = solve_flexible_subset(
                        my_numbers,
                        target_1,
                        target_2,
                        target_3
                    )

                    # 根据是否启用第三目标，拼接最终顺序
                    if use_third_target:
                        final_arrangement = part1 + part2 + part3 + remain
                    else:
                        final_arrangement = part1 + part2 + remain

                    output_text = "\n".join(
                        str(x) for x in final_arrangement
                    )

                    # 累计和
                    sum1 = sum(part1)
                    sum2 = sum1 + sum(part2)
                    sum3 = sum2 + sum(part3)

                    if use_third_target:
                        st.success(
                            f"第一阶段：{len(part1)} 个数字，"
                            f"累计和 {sum1:,.2f}\n\n"
                            f"第二阶段：{len(part2)} 个数字，"
                            f"累计和 {sum2:,.2f}\n\n"
                            f"第三阶段：{len(part3)} 个数字，"
                            f"累计和 {sum3:,.2f}\n\n"
                            f"第四阶段：剩余 {len(remain)} 个数字，"
                            f"合计 {sum(remain):,.2f}"
                        )
                    else:
                        st.success(
                            f"第一阶段：{len(part1)} 个数字，"
                            f"累计和 {sum1:,.2f}\n\n"
                            f"第二阶段：{len(part2)} 个数字，"
                            f"累计和 {sum2:,.2f}\n\n"
                            f"第三阶段：剩余 {len(remain)} 个数字，"
                            f"合计 {sum(remain):,.2f}"
                        )

                    st.text_area(
                        "最终推荐的完整排列顺序"
                        "（可直接全选复制，贴回 Excel）：",
                        value=output_text,
                        height=350,
                    )

                    with st.expander("🔍 查看划分详情"):
                        st.write(
                            f"**第一阶段（{len(part1)} 个）：** {part1}"
                        )
                        st.write(
                            f"**第一阶段累计和：** {sum1:,.2f}，"
                            f"目标：{target_1:,.2f}"
                        )

                        st.write(
                            f"**第二阶段追加（{len(part2)} 个）：** {part2}"
                        )
                        st.write(
                            f"**第二阶段累计和：** {sum2:,.2f}，"
                            f"目标：{target_2:,.2f}"
                        )

                        if use_third_target:
                            st.write(
                                f"**第三阶段追加（{len(part3)} 个）：** "
                                f"{part3}"
                            )
                            st.write(
                                f"**第三阶段累计和：** {sum3:,.2f}，"
                                f"目标：{target_3:,.2f}"
                            )

                        st.write(
                            f"**剩余数字（{len(remain)} 个）：** {remain}"
                        )
                        st.write(
                            f"**剩余数字合计：** {sum(remain):,.2f}"
                        )

                except Exception as e:
                    st.error(f"计算失败：{e}")

    else:
        st.info("💡 请在左侧输入框内粘贴数字。")
