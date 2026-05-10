import json
import os

designs_dir = '/Users/muyaowu/Documents/PhrollerDesign/PhrollerDesigns/assets/designs'
files = [f for f in os.listdir(designs_dir) if f.endswith('.json')]

physics_keys = ['globalFriction', 'slidingDamping', 'globalBounciness', 'drag']

for filename in files:
    path = os.path.join(designs_dir, filename)
    print(f"Processing {filename}...")
    
    with open(path, 'r') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"  Error loading {filename}: {e}")
            continue
    
    # Empty groups in preset
    if 'preset' in data and data['preset'] is not None:
        data['preset']['groups'] = []
    else:
        data['preset'] = {"name": data.get('settings', {}).get('name', 'Default'), "groups": []}
    
    # Set arsenalDice to empty list
    data['arsenalDice'] = []
    
    # Remove physics settings
    if 'settings' in data:
        for key in physics_keys:
            if key in data['settings']:
                del data['settings'][key]
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

print("Done!")
