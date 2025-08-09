import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import json
import pandas as pd
from datetime import datetime


with open("../data/recorded_sequence.json", 'r') as f:
    data = json.load(f)
# with open("fixed_recorded_sequence-2.json", 'r') as f:
#     data.extend(json.load(f))
# with open("fixed_recorded_sequence-3.json", 'r') as f:
#     data.extend(json.load(f))

pd.DataFrame(data).to_csv(f"../data/data_{datetime.now().strftime('%Y%m%dT%H%M%S')}.csv")

press_keys = []
press_delays = []
for i in range(1, len(data)):
    if data[i]['key'] not in ['Key.left', 'Key.right'] and \
            data[i]['key'] == data[i - 1]['key'] and \
            data[i]['event'] == 'keyup' and \
            data[i - 1]['event'] == 'keydown':
        press_keys.append(data[i]['key'])
        press_delays.append(data[i]['delay'])

pd.DataFrame({'keys': press_keys, 'delays': press_delays}).sort_values('delays').to_csv("temp_data.csv")


plt.hist(press_delays, bins=100, edgecolor='black')
plt.title("Key Press Duration Histogram")
plt.xlim([0, 0.4])
plt.xlabel("Duration (seconds)")
plt.ylabel("Frequency")
plt.grid(True)
plt.show()