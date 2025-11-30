import streamlit as st
import numpy as np
import time
import plotly.graph_objects as go
import pandas as pd

# ------------------ Disk Algorithms ---------------------

def fcfs(requests, head):
    order = [head] + requests
    total = sum(abs(order[i] - order[i - 1]) for i in range(1, len(order)))
    return order, total

def sstf(requests, head):
    reqs = requests.copy()
    order = [head]
    current = head

    while reqs:
        nearest = min(reqs, key=lambda x: abs(x - current))
        order.append(nearest)
        reqs.remove(nearest)
        current = nearest
    
    total = sum(abs(order[i] - order[i - 1]) for i in range(1, len(order)))
    return order, total

def scan(requests, head, disk_size=200, direction="right"):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    order = [head]

    if direction == "right":
        # Move right → end → reverse to left
        order += right + [disk_size - 1] + left[::-1]
    else:
        # Move left → start → reverse to right
        order += left[::-1] + [0] + right

    total = sum(abs(order[i] - order[i - 1]) for i in range(1, len(order)))
    return order, total


def c_scan(requests, head, disk_size=200, direction="right"):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    if direction == "right":   # Clockwise →
        order = [head] + right + [disk_size - 1, 0] + left
    else:                      # Anti-Clockwise ←
        order = [head] + left[::-1] + [0, disk_size - 1] + right[::-1]

    total = sum(abs(order[i] - order[i - 1]) for i in range(1, len(order)))
    return order, total


# ------------------ Animation ---------------------

def animate(order,speed):
    st.write("### 🎬 Disk Head Animation")
    fig = go.Figure()

    for i in range(1, len(order)):
        fig.add_trace(go.Scatter(
            x=[order[i - 1], order[i]],
            y=[0, 0],
            mode="lines+markers+text",
            text=[order[i - 1], order[i]],
            textposition="top center"
        ))

        st.plotly_chart(fig, use_container_width=True)
        time.sleep(speed)

# ------------------ UI ---------------------

st.title("🚀 Advanced Disk Scheduling Simulator")

req_str = st.text_input("Enter disk requests", "82, 170, 43, 140, 24, 16, 190")
head = st.number_input("Starting head position", 0, 500, 50)
disk_size = st.number_input("Disk Size (Cylinders)", 100, 1000, 200)

# Validate Input Requests
def parse_requests(req_str):
    try:
        req_list = list(map(int, req_str.replace(" ", "").split(",")))
        return req_list
    except:
        st.error("❌ Invalid input! Enter numbers separated by commas.")
        return None

# Random Request Generator
if st.button("🎲 Generate Random Requests"):
    import random
    req_str = ", ".join(map(str, random.sample(range(0, disk_size), 8)))
    st.success(f"✅ Random Requests Generated: {req_str}")

algorithms = {
    "FCFS": fcfs,
    "SSTF": sstf,
    "SCAN": scan,
    "C-SCAN": c_scan,
}
algo = st.selectbox("Select Algorithm", list(algorithms.keys()))
speed = st.selectbox(
    "⚡ Animation Speed (sec per move)",
    [0.1,0.5,1, 2, 3, 4, 5],
    index=0
)


# Direction selectors (shown only when relevant)
scan_direction = None
cscan_direction = None
if algo == "SCAN":
    scan_direction = st.selectbox("Scan direction", ["right", "left"])   # user picks initial movement
elif algo == "C-SCAN":
    cscan_direction = st.selectbox("C-SCAN direction", ["right", "left"]) # clockwise (right) or anticlockwise (left)

# Update SCAN dynamically after direction is known
def get_algorithm_callable(algo_name):
    # for SCAN / C-SCAN we must provide direction captured from UI
    if algo_name == "SCAN":
        # default to 'right' if somehow none selected
        dir_sel = "right" if scan_direction is None else scan_direction
        return lambda r, h: scan(r, h, disk_size, dir_sel)
    if algo_name == "C-SCAN":
        dir_sel = "right" if cscan_direction is None else cscan_direction
        return lambda r, h: c_scan(r, h, disk_size, dir_sel)
    return algorithms[algo_name]


if st.button("Run Simulation"):

    # Convert request string to list
    requests = list(map(int, req_str.split(',')))

    # SELECT ALGORITHM
    if algo == "SCAN":
        direction = scan_direction
        order, total = scan(requests, head, disk_size, direction)

    elif algo == "C-SCAN":
        direction = cscan_direction
        order, total = c_scan(requests, head, disk_size, direction)

    else:
        selected_algo = algorithms[algo]
        order, total = selected_algo(requests, head)

    # DISPLAY RESULTS
    avg_seek = total / len(requests)
    throughput = len(requests) / total if total != 0 else 0

    st.success(f"✅ Algorithm: {algo}")
    st.write(f"📌 **Sequence**: {order}")
    st.write(f"📊 **Total Seek Time**: {total}")
    st.write(f"⚙️ **Average Seek Time** = {avg_seek:.2f}")
    st.write(f"🚀 **System Throughput** = {throughput:.4f} requests/unit time")

    animate(order, speed)


if st.button("Compare All Algorithms"):
    
    request_list = list(map(int, req_str.split(',')))
    results = {}
    orders = {}
    
    for name, fn in algorithms.items():
        if name == "SCAN":
            order, total = scan(request_list, head, disk_size, "right")
        elif name == "C-SCAN":
            order, total = c_scan(request_list, head, disk_size, "right")
        else:
            order, total = fn(request_list, head)
    
        results[name] = total
        orders[name] = order

    st.subheader("🔎 Performance Comparison")

    # Display Table
    st.table({
        "Algorithm": list(results.keys()),
        "Total Seek Time": list(results.values()),
        "Avg SeekTime": [results[a] / len(request_list) for a in results],
        "Throughput": [len(request_list) / results[a] if results[a] != 0 else 0 for a in results]
    })

    # 📊 Bar Chart
    fig = go.Figure(data=[go.Bar(x=list(results.keys()), y=list(results.values()))])
    fig.update_layout(title="Seek Time Comparison", xaxis_title="Algorithm", yaxis_title="Total Seek Time")
    st.plotly_chart(fig, use_container_width=True)

    # 📈 Line Chart for Movement
    for name, order in orders.items():
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=list(range(len(order))), y=order, mode="lines+markers"))
        fig2.update_layout(title=f"Head Movement Pattern ({name})",
                           xaxis_title="Step",
                           yaxis_title="Cylinder Number")
        st.plotly_chart(fig2, use_container_width=True)

    # ✅ Export Table to CSV
    df = pd.DataFrame({
        "Algorithm": list(results.keys()),
        "Total Seek Time": list(results.values()),
        "Average Seek Time": [results[a]/len(request_list) for a in results],
        "Throughput (req/unit time)": [len(request_list) / results[a] if results[a] != 0 else 0 for a in results]

    })

    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Result as CSV",
        data=csv,
        file_name="disk_scheduling_results.csv",
        mime='text/csv',
    )


if st.button("🔄 Reset"):
    st.rerun()



