import json
import os

designs_dir = '/Users/muyaowu/Documents/PhrollerDesign/PhrollerDesigns/assets/designs'
files = [f for f in os.listdir(designs_dir) if f.endswith('.json')]

global_physics_keys = ['globalFriction', 'slidingDamping', 'globalBounciness', 'drag']
dice_physics_keys = ['mass', 'bounciness', 'friction', 'drag', 'slidingDamping']

def cleanup_dice_data(dice_data):
    if not isinstance(dice_data, dict):
        return
    for key in dice_physics_keys:
        if key in dice_data:
            del dice_data[key]

for filename in files:
    path = os.path.join(designs_dir, filename)
    print(f"Processing {filename}...")
    
    with open(path, 'r') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"  Error loading {filename}: {e}")
            continue
    
    # 1. Cleanup physics in settings
    if 'settings' in data:
        for key in global_physics_keys:
            if key in data['settings']:
                del data['settings'][key]
    
    # 2. Cleanup physics in preset.groups
    if 'preset' in data and data['preset'] is not None:
        groups = data['preset'].get('groups', [])
        for group in groups:
            if 'diceTypeData' in group:
                cleanup_dice_data(group['diceTypeData'])
    
    # 3. Cleanup physics in arsenalDice
    if 'arsenalDice' in data and data['arsenalDice'] is not None:
        for dice in data['arsenalDice']:
            cleanup_dice_data(dice)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

print("Done!")
