import json

with open('final_results.json') as f:
    results = json.load(f)

speaker_moot_points = {}

for result in results:
    speaker = result['speaker']

    if speaker not in speaker_moot_points:
        speaker_moot_points[speaker] = {
            "moot_points": {},
            "side": result['side']
        }
    
    speaker_positions = speaker_moot_points[speaker]["moot_points"]

    for moot_point, position in result['refed_moot_points'].items():
        if moot_point in speaker_positions:
            speaker_positions[moot_point].append(position)
        else:
            speaker_positions[moot_point] = [position]

changing_positions = {}

for speaker in speaker_moot_points:
    moot_points = {}

    for moot_point, positions in speaker_moot_points[speaker]["moot_points"].items():
        if len(positions) > 1:
            moot_points[moot_point] = positions

    if len(moot_points) > 0:
        changing_positions[speaker] = {
            "moot_points": moot_points,
            "side": speaker_moot_points[speaker]["side"]
        }

all_references = 0
speakers = 0

for speaker, data in changing_positions.items():
    all_references += len(data['moot_points'])
    speakers += 1

with open('changing_positions.json', 'w', encoding='utf-8') as f:
    json.dump(changing_positions, f, ensure_ascii=False, indent='\t')
