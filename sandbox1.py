import matplotlib.pyplot as plt
import pprint
pp = pprint.PrettyPrinter(indent=4)

### NOTES:
### For N sidings:
### 2N-1 max trains on the track at once.
### N trains max in either direction at once.
### Probably best to just assume a max of N-1 trains in either direction at once






## Prepare some scenario data:
colors = {
	"n":"blue",
	"s":"red",
}
markers = {
	"n":"o",
	"s":"s",
}
trackLength = 200
sidingMiles = [25,50,75,100,125,150,175]
sidings = {}
for sm in sidingMiles:
    sidings[sm] = { "mile":sm, "train":False }
segments = {}
for i in sidingMiles:
    s = str(i-25)+"-"+str(i)
    segments[s] = { "min":i-25, "max":i, "trains":{"n":{}, "s":{} } }
s = str(sidingMiles[len(sidingMiles)-1])+"-"+str(trackLength)
segments[s] = { "min":sidingMiles[len(sidingMiles)-1], "max":trackLength, "trains":{"n":{}, "s":{} } }

mph = 30
totalMinutes = 15 # 48*60
nTrainsPerDirection = 3
dispatchInterval = totalMinutes/nTrainsPerDirection
minutesPerMile = 60/mph
milesPerMinute = mph/60
dispatches = []
d = 0
while(d<totalMinutes):
    dispatches.append(int(d))
    d += dispatchInterval



trains = {"s":{}, "n":{}}
for i in range(0,nTrainsPerDirection):
    trains["s"]["s"+str(i+1)] = {
        "direction":"s",
        "dispatch":dispatches[i],
        "mph":mph,
        "position":trackLength,
        "dispatched":False,
        "nextCollision":False,
        "waiting":0,
    }
    trains["n"]["n"+str(i+1)] = {
        "direction":"n",
        "dispatch":dispatches[i],
        "mph":mph,
        "position":0,
        "dispatched":False,
        "nextCollision":False,
        "waiting":0,
    }






def determineTrainSegment(train):
    if (train["moving"]):
        for s, segment in segments.items():
            if (train["direction"]=="n"):
                if (segment["min"] < train["position"] <= segment["max"]):
                    return segment
            if (train["direction"]=="s"):
                if (segment["min"] <= train["position"] < segment["max"]):
                    return segment
    return False

def determineTrainSiding(train):
    if (train["moving"]):
        for s, siding in sidings.items():
            if (siding["mile"] == train["position"]):
                return siding
    return False


## Determine meeting point and closest siding:
def find_meeting_point(train1, train2, sidings):
    # Extract values
    p1, d1, v1 = train1["position"], train1["direction"].upper(), train1["mph"]
    p2, d2, v2 = train2["position"], train2["direction"].upper(), train2["mph"]
    # Validate input
    if d1 == d2:
        raise ValueError("Trains are moving in the same direction, they won't meet.")
    if not ((d1 == 'N' and d2 == 'S' and p1 < p2) or
            (d1 == 'S' and d2 == 'N' and p2 < p1)):
        raise ValueError("Train directions or positions are inconsistent with a meeting path.")
    # Distance and time to meet
    distance = abs(p1 - p2)
    time_to_meet = distance / (v1 + v2)
    move1 = v1 * time_to_meet
    # Meeting point and track bounds
    if d1 == 'N':
        meeting_point = p1 + move1
        lower_bound, upper_bound = p1, p2
    else:
        meeting_point = p1 - move1
        lower_bound, upper_bound = p2, p1
    # Filter sidings that are between the two trains
    in_range_sidings = [s for s in sidings if lower_bound <= s <= upper_bound]
    # Find closest if any
    closest_siding = min(in_range_sidings, key=lambda s: abs(s - meeting_point)) if in_range_sidings else False
    return {
        "miles": meeting_point,
        "siding": closest_siding
    }








"""
pp.pprint(segments)
pp.pprint(sidings)

trains["n"]["n1"]["position"] = 57
trains["n"]["n2"]["position"] = 25
trains["s"]["s1"]["position"] = 135
trains["s"]["s2"]["position"] = 175
trains["n"]["n1"]["moving"] = True
trains["n"]["n2"]["moving"] = True
trains["s"]["s1"]["moving"] = True
trains["s"]["s2"]["moving"] = True
print(trains["n"]["n1"]["position"], determineTrainSegment(trains["n"]["n1"]))
print(trains["n"]["n2"]["position"], determineTrainSegment(trains["n"]["n2"]))
print(trains["s"]["s1"]["position"], determineTrainSegment(trains["s"]["s1"]))
print(trains["s"]["s2"]["position"], determineTrainSegment(trains["s"]["s2"]))
print(trains["n"]["n1"]["position"], determineTrainSiding(trains["n"]["n1"]))
print(trains["n"]["n2"]["position"], determineTrainSiding(trains["n"]["n2"]))
print(trains["s"]["s1"]["position"], determineTrainSiding(trains["s"]["s1"]))
print(trains["s"]["s2"]["position"], determineTrainSiding(trains["s"]["s2"]))
"""




def dispatchTrains(minute):
    if (len(dispatches)>0):
        d = dispatches[0]
        if (minute >= d):
            for direction in trains:
                for t, train in trains[direction].items():
                    print(minute, d, train["dispatch"])
                    if (train["dispatch"] <= minute):
                        trains[direction][t]["dispatched"] = True
            del dispatches[0]
            return d
    return False


## LOOP BY MINUTE:
for minute in range(totalMinutes):
    d = dispatchTrains(minute)
    if (d):
        pp.pprint(trains)
        print("-------------")


exit()






def dispatchTrains(dispatch):
    for d,dTrain in trains.items():
        for t,train in dTrain.items():
            ## Only allow a train if there are fewer than len(sidings)-1 on the track so far:
            if ( len(transit[d]) < len(sidings)-1 ):
                ## Add the train to the transit if not already there:
                ## We'll toggle it to False when it finishes up
                if t not in transit[d]:
                    if (train["dispatch"]==dispatch and not train["dispatched"]):
                        transit[d].append(t)
                        trains[d][t]["dispatched"] = True
    



transit = {"n":[],"s":[]}

## MAIN LOOP:

for dispatch in dispatches:
    print("dispatch:", dispatch)
    dispatchTrains(dispatch)
    print("Transits:")
    pp.pprint(transit)
    print("Upcoming Collisions:")
    if ( len(transit["n"])>0 and len(transit["s"])>0 ):
        cc = 0
        for nTrain in transit["n"]:
            for sTrain in transit["s"]:
                cc += 1
                print(cc)
                mp = find_meeting_point(trains["n"][nTrain], trains["s"][sTrain], sidings)
                pp.pprint(mp)
                nTrainDist = abs(trains["n"][nTrain]["position"] - mp["miles"])
                print("nTrainDist:", nTrainDist)
                sTrainDist = abs(trains["s"][sTrain]["position"] - mp["miles"])
                print("nTrainDist:", nTrainDist)


    print("--------------------------------------")


"""
# Create the plot
plt.figure(figsize=(8, 5))

# Plot each line
for train in trains:
	plt.plot(x, [], label='N1', color=colors["n"], marker=markers[train["direction"]])


# Add labels and title
plt.xlabel('Minutes')
plt.ylabel('Miles')
plt.title('Train Crossings')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()
"""
