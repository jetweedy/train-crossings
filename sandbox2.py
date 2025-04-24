def schedule_trains(trains, sidings, track_length):
    # Preprocess trains with positions and velocity in miles/minute
    scheduled = []
    for train in trains:
        direction = train["direction"].lower()
        speed_mpm = train["mph"] / 60  # miles per minute
        dispatch_min = train["dispatchMinutes"]
        start_pos = 0 if direction == "north" else track_length
        train_data = {
            **train,
            "start_pos": start_pos,
            "velocity": speed_mpm if direction == "north" else -speed_mpm,
            "active": True,
            "id": f"Train_{len(scheduled)}",
        }
        scheduled.append(train_data)

    # Sort sidings for convenience
    sidings = sorted(sidings)

    # Simulation step
    time = 0
    positions = {t["id"]: None for t in scheduled}
    waiting = {s: None for s in sidings}
    conflicts = []

    while any(t["active"] for t in scheduled):
        time += 1  # step in minutes

        # Update positions
        for t in scheduled:
            if not t["active"]:
                continue
            if time < t["dispatchMinutes"]:
                continue  # not yet dispatched

            # Calculate current position
            delta_time = time - t["dispatchMinutes"]
            pos = t["start_pos"] + delta_time * t["velocity"]
            positions[t["id"]] = pos

            # Check if off the track
            if not (0 <= pos <= track_length):
                t["active"] = False

        # Check for conflicts and resolve
        ids = list(positions.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                t1, t2 = ids[i], ids[j]
                pos1, pos2 = positions[t1], positions[t2]
                if pos1 is None or pos2 is None:
                    continue
                if abs(pos1 - pos2) < 0.25:  # collision proximity
                    # Conflict detected
                    conflicts.append((time, t1, t2, pos1))
                    # Nearest siding
                    midpoint = (pos1 + pos2) / 2
                    available_sidings = [s for s in sidings if s >= min(pos1, pos2) and s <= max(pos1, pos2)]
                    if not available_sidings:
                        continue  # no siding, can't resolve

                    siding = min(available_sidings, key=lambda s: abs(s - midpoint))
                    # Assign one train to wait
                    if waiting[siding] is None:
                        waiting[siding] = t1
                        positions[t1] = siding  # freeze one train at siding
                        scheduled[[t["id"] for t in scheduled].index(t1)]["active"] = False  # simplification

    return {
        "finalPositions": positions,
        "conflicts": conflicts,
        "sidingsUsed": [s for s, t in waiting.items() if t],
    }




trains = [
    {"direction": "north", "mph": 30, "dispatchMinutes": 0},
    {"direction": "south", "mph": 30, "dispatchMinutes": 5},
    {"direction": "north", "mph": 40, "dispatchMinutes": 10}
]

sidings = [20, 50, 80, 120]
track_length = 150

result = schedule_trains(trains, sidings, track_length)
print(result)
