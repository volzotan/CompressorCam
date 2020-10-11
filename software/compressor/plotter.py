import matplotlib.pyplot as plt
import json

JSON_FILES  = [
    "translation_data_noReset_yesDownsize.json", 
    "translation_data_yesReset_yesDownsize.json", 
    "translation_data_noReset_noDownsize.json", 
    "translation_data_yesReset_noDownsize.json", 
    "translation_data.json"
]

datasets        = {}

for f in JSON_FILES:
    try:
        datasets[f] = json.load(open(f, "r"))
    except IOError as e:
        print("missing: {}".format(f))

plots = {}

for dataset in datasets:
    x = []
    y = []

    for image in datasets[dataset]:
        x.append(datasets[dataset][image][1][0])
        y.append(datasets[dataset][image][1][1])

    plots[dataset] = (x,y)

plt.subplot(211)
plt.title('Horizontal')
for plotdata in plots:
    print plotdata
    plt.plot(plots[plotdata][0], alpha=0.5, label=plotdata)

plt.grid(linestyle='dashed', linewidth=0.5, alpha=.3)

plt.subplot(212)
plt.title('Vertical')
for plotdata in plots:
    plt.plot(plots[plotdata][1], alpha=0.5, label=plotdata)

plt.grid(linestyle='dashed', linewidth=0.5, alpha=.3)

plt.show()

