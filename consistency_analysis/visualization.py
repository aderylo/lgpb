import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

with open('changing_positions.json') as f:
    speaker_positions = json.load(f)

records = []

for speaker, data in speaker_positions.items():
    side = data["side"]
    moot_points = data["moot_points"]
    for moot_point, positions in moot_points.items():
        for idx, position in enumerate(positions):
            records.append({
                "speaker": speaker,
                "side": side,
                "moot_point": moot_point,
                "order": idx,
                "position": position
            })

df = pd.DataFrame(records)

position_mapping = {"negative": -1, "neutral": 0, "positive": 1}

df["position_value"] = df["position"].map(position_mapping)

def calculate_consistency_and_magnitudes(positions):
    if len(positions) < 2:
        return 1, 0
    
    changes = sum(1 for i in range (1, len(positions)) if positions[i] != positions[i-1])
    total_changes = len(positions) - 1
    consistency = 1 - changes / total_changes

    magnitudes = [abs(positions[i] - positions[i-1]) for i in range(1, len(positions))]
    magnitude = sum(magnitudes) / (2*total_changes)

    return consistency, magnitude

def visualise(data, column, xlabel, title, save_name):
    fig, ax1 = plt.subplots(figsize=(14, 7))

    sns.barplot(x=column, y="consistency_score", data=data, ax=ax1, palette="muted")
    ax1.set_ylabel("Średnia wartość konsystencji")
    ax1.set_ylim(0, 1.2)
    ax1.set_title(title)

    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
    plt.xlabel(xlabel)

    ax2 = ax1.twinx()
    sns.lineplot(x=column, y="magnitude", data=data, ax=ax2, marker="o", color="r", linestyle="--")
    ax2.set_ylabel("Średnia wartość wielkości zmian")
    ax2.set_ylim(0, max(data["magnitude"]) + 0.5)

    plt.savefig(save_name, bbox_inches="tight")

results = df.groupby(["speaker", "side", "moot_point"])["position_value"].apply(list).apply(lambda x: pd.Series(calculate_consistency_and_magnitudes(x))).reset_index()
results.columns = ["speaker", "side", "moot_point", "consistency_score", "magnitude"]

average_speaker_scores = results.groupby(["speaker"])[["consistency_score", "magnitude"]].mean().reset_index()
average_side_scores = results.groupby(["side"])[["consistency_score", "magnitude"]].mean().reset_index()

visualise(average_speaker_scores, "speaker", "Mówca", "Średnia wartość konsystencji oraz wielkości zmian pozycji mówców", "consistency_and_magnitude_speakers_plot.png")
visualise(average_side_scores, "side", "Strona", "Średnia wartość konsystencji oraz wielkości zmian pozycji stron", "consistency_and_magnitude_sides_plot.png")

plt.show()