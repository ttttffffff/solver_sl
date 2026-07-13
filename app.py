import pulp
import streamlit as st

# 设置网页标题和布局（宽屏模式，方便左右对比）
st.set_page_config(page_title="极简数字凑数工具", layout="wide")

st.title("📊 极简数字凑数工具 (Excel 复制即用版)")
st.markdown("---")

# ==================== 核心算法逻辑 ====================
def solve_flexible_subset(numbers, target_1, target_2):
    total_len = len(numbers)
    prob = pulp.LpProblem("Flexible_Subset_Optimization", pulp.LpMinimize)

    y1 = pulp.LpVariable.dicts("y1", range(total_len), cat="Binary")
    y2 = pulp.LpVariable.dicts("y2", range(total_len), cat="Binary")

    d1_pos = pulp.LpVariable("d1_pos", lowBound=0)
    d1_neg = pulp.LpVariable("d1_neg", lowBound=0)
    d2_pos = pulp.LpVariable("d2_pos", lowBound=0)
    d2_neg = pulp.LpVariable("d2_neg", lowBound=0)

    prob += d1_pos + d1_neg + d2_pos + d2_neg

    for i in range(total_len):
        prob += y1[i] + y2[i] <= 1

    sum_part1 = pulp.lpSum(numbers[i] * y1[i] for i in range(total_len))
    prob += sum_part1 - target_1 == d1_pos - d1_neg

    sum_part2 = pulp.lpSum(numbers[i] * y2[i] for i in range(total_len))
    prob += (sum_part1 + sum_part2) - target_2 == d2_pos - d2_neg

    # prob.solve(pulp.PULP_CBC_CMD(msg=False))
    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=60, gapRel=0.001))

    part1_list = [
        numbers[i] for i in range(total_len) if pulp.value(y1[i]) == 1
    ]
    part2_list = [
        numbers[i] for i in range(total_len) if pulp.value(y2[i]) == 1
    ]
    remain_list = [
        numbers[i]
        for i in range(total_len)
        # if pulp.value(y1[i]) == 0 and pulp.value(y2[i]) == 0
        if (pulp.value(y1[i]) or 0) < 0.5 and (pulp.value(y2[i]) or 0) < 0.5
    ]

    return part1_list, part2_list, remain_list


# ==================== 界面布局 ====================
# 使用两列布局：左边输入，右边输出
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📥 输入数据与参数")

    # 目标值设置
    target_1 = st.number_input("第一阶段目标和", value=35000, step=1000)
    target_2 = st.number_input("第二阶段总目标和", value=50000, step=1000)

    # 默认提供一些测试数据，方便看效果
    default_input = "2761\n2507\n2124\n1860\n2248.5\n1912.5\n1562\n2059.5"
    user_input = st.text_area(
        "请在此粘贴从 Excel 复制的数字列（每行一个数字）：",
        value=default_input,
        height=400,
    )

    # 解析输入的文本
    my_numbers = []
    if user_input:
        # 按换行符切分，并过滤掉空行
        lines = user_input.split("\n")
        try:
            my_numbers = [float(line.strip()) for line in lines if line.strip()]
        except ValueError:
            st.error(
                "⚠️ 解析失败！输入框中包含非数字内容，请检查是否有文字或特殊符号。"
            )

    # 显示当前解析状态
    if my_numbers:
        st.caption(
            f"✅ 成功识别 **{len(my_numbers)}** 个数字，当前总和为: {sum(my_numbers):,.2f}"
        )

with col_right:
    st.subheader("📤 求解结果 (直接复制)")

    # 只有当有有效数字，且用户点击按钮时才触发计算
    if my_numbers:
        if st.button("🚀 开始智能计算", type="primary", use_container_width=True):
            with st.spinner("计算中..."):
                part1, part2, remain = solve_flexible_subset(
                    my_numbers, target_1, target_2
                )

                # 拼接成最终推荐的完整排序列表
                final_arrangement = part1 + part2 + remain

                # 将结果转换为换行符分隔的文本格式
                output_text = "\n".join(str(x) for x in final_arrangement)

                # 简要的数据指标反馈
                st.success(
                    f"💡 第一阶段选了 {len(part1)} 个数 (和: {sum(part1):,.1f}) \n\n "
                    f"追加后前 m 个数总和: {sum(part1) + sum(part2):,.1f}"
                )

                # 用另一个 text_area 把结果吐出来，方便用户一键全选复制
                st.text_area(
                    "最终推荐的完整排列顺序（可直接全选复制，贴回 Excel）：",
                    value=output_text,
                    height=350,
                )

                # 额外附赠一个提示，方便了解各数字去了哪里
                with st.expander("🔍 查看划分详情"):
                    st.write(f"**第一阶段入选 ({len(part1)}个)：** {part1}")
                    st.write(f"**第二阶段追加 ({len(part2)}个)：** {part2}")
                    st.write(f"**未选中的余数 ({len(remain)}个)：** {remain}")
    else:
        st.info("💡 请在左侧输入框内粘贴数字。")