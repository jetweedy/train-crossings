from pyomo.environ import *
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

model = ConcreteModel()

# Time and space definitions
timeSteps = 60  # Increased time for trains to complete trips
numTrainsEach = 3  # Fewer trains for easier passage
NODES = range(0, 9)
SIDINGS = [1, 2, 3, 4, 5, 6, 7]
T = range(0, timeSteps)
dispatchInterval = timeSteps // numTrainsEach

# Train sets per direction
TRAINS_NS = range(0, numTrainsEach)
TRAINS_SN = range(0, numTrainsEach)
track_length = max(NODES)

# Dispatch times
dispatch_time_NS = {t: int(t * dispatchInterval) for t in TRAINS_NS}
dispatch_time_SN = {t: int(t * dispatchInterval) for t in TRAINS_SN}

# Variables
model.x = Var(TRAINS_NS, NODES, T, domain=Binary)
model.y = Var(TRAINS_SN, NODES, T, domain=Binary)
model.z_NS = Var(TRAINS_NS, domain=Binary)
model.z_SN = Var(TRAINS_SN, domain=Binary)
model.wait_NS = Var(TRAINS_NS, NODES, T, domain=Binary)
model.wait_SN = Var(TRAINS_SN, NODES, T, domain=Binary)

# Constraints (same as before)
def node_capacity(model, n, t):
    return sum(model.x[k, n, t] for k in TRAINS_NS) + sum(model.y[k, n, t] for k in TRAINS_SN) <= 1
model.node_capacity = Constraint(NODES, T, rule=node_capacity)

def flow_conservation_NS(model, k, n, t):
    if t == 0:
        return Constraint.Skip
    prev_nodes = [n]
    if n > 0:
        prev_nodes.append(n - 1)
    return model.x[k, n, t] <= sum(model.x[k, pn, t - 1] for pn in prev_nodes)
model.flow_NS = Constraint(TRAINS_NS, NODES, T, rule=flow_conservation_NS)

def flow_conservation_SN(model, k, n, t):
    if t == 0:
        return Constraint.Skip
    prev_nodes = [n]
    if n < track_length:
        prev_nodes.append(n + 1)
    return model.y[k, n, t] <= sum(model.y[k, pn, t - 1] for pn in prev_nodes)
model.flow_SN = Constraint(TRAINS_SN, NODES, T, rule=flow_conservation_SN)

# Dispatch & End
model.start_NS = Constraint(TRAINS_NS, rule=lambda m, k: m.x[k, 0, dispatch_time_NS[k]] == 1)
model.start_SN = Constraint(TRAINS_SN, rule=lambda m, k: m.y[k, track_length, dispatch_time_SN[k]] == 1)
model.end_NS = Constraint(TRAINS_NS, rule=lambda m, k: m.z_NS[k] <= sum(m.x[k, track_length, t] for t in T))
model.end_SN = Constraint(TRAINS_SN, rule=lambda m, k: m.z_SN[k] <= sum(m.y[k, 0, t] for t in T))

# Waiting only in sidings
model.wait_only_NS = ConstraintList()
model.wait_only_SN = ConstraintList()
for k in TRAINS_NS:
    for n in NODES:
        if n not in SIDINGS:
            for t in T:
                model.wait_only_NS.add(model.wait_NS[k, n, t] == 0)
for k in TRAINS_SN:
    for n in NODES:
        if n not in SIDINGS:
            for t in T:
                model.wait_only_SN.add(model.wait_SN[k, n, t] == 0)

# Detect waiting
model.detect_wait_NS = ConstraintList()
for k in TRAINS_NS:
    for n in NODES:
        for t in T:
            if t > 0:
                model.detect_wait_NS.add(model.wait_NS[k, n, t] >= model.x[k, n, t] + model.x[k, n, t - 1] - 1)

model.detect_wait_SN = ConstraintList()
for k in TRAINS_SN:
    for n in NODES:
        for t in T:
            if t > 0:
                model.detect_wait_SN.add(model.wait_SN[k, n, t] >= model.y[k, n, t] + model.y[k, n, t - 1] - 1)


# Conflict avoidance
model.pass_conflict = ConstraintList()
for n in NODES:
    for t in T:
        for k1 in TRAINS_NS:
            for k2 in TRAINS_SN:
                if 0 < n < track_length:
                    model.pass_conflict.add(
                        model.x[k1, n, t] + model.y[k2, n, t] <= model.wait_NS[k1, n, t] + model.wait_SN[k2, n, t] + 1)
                    model.pass_conflict.add(
                        model.x[k1, n, t] + model.y[k2, n - 1, t] <= model.wait_NS[k1, n, t] + model.wait_SN[k2, n - 1, t] + 1)
                    model.pass_conflict.add(
                        model.x[k1, n, t] + model.y[k2, n + 1, t] <= model.wait_NS[k1, n, t] + model.wait_SN[k2, n + 1, t] + 1)

# Objective
model.obj = Objective(expr=sum(model.z_NS[k] for k in TRAINS_NS) + sum(model.z_SN[k] for k in TRAINS_SN), sense=maximize)

# Debug after solving
from pyomo.opt import SolverFactory
solver = SolverFactory("glpk")
result = solver.solve(model)

print("Solver status:", result.solver.status)
print("Solver termination condition:", result.solver.termination_condition)
try:
    print("Objective value:", value(model.obj))
except Exception as e:
    print("Error evaluating objective:", e)

# Extract and plot
rows = []
for k in TRAINS_NS:
    for n in NODES:
        for t in T:
            if model.x[k, n, t].value == 1:
                rows.append(("NS", k, n, t))
for k in TRAINS_SN:
    for n in NODES:
        for t in T:
            if model.y[k, n, t].value == 1:
                rows.append(("SN", k, n, t))
df = pd.DataFrame(rows, columns=["Direction", "TrainID", "Node", "Time"])
print(f"Scheduled positions: {len(df)}")

if not df.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    cmap_ns = cm.Blues(np.linspace(0.4, 0.9, len(df[df['Direction'] == 'NS']['TrainID'].unique())))
    cmap_sn = cm.Reds(np.linspace(0.4, 0.9, len(df[df['Direction'] == 'SN']['TrainID'].unique())))
    for i, (direction, train) in enumerate(df.groupby(["Direction", "TrainID"]).groups.keys()):
        group = df[(df.Direction == direction) & (df.TrainID == train)]
        color = cmap_ns[train] if direction == "NS" else cmap_sn[train]
        ax.plot(group["Time"], group["Node"], marker='o', label=f"{direction} {train}", color=color)
    for siding in SIDINGS:
        ax.axhline(y=siding, color='gray', linestyle='--', alpha=0.4)
        ax.text(df['Time'].max() + 0.5, siding, f"Siding {siding}", va='center', fontsize=9)
    ax.set_xlabel("Time")
    ax.set_ylabel("Track Node")
    ax.set_title("Train Movements Over Time (Gantt-style)")
    ax.legend()
    ax.invert_yaxis()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    print("No trains were scheduled. Adjust constraints or time horizon.")
