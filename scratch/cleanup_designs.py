import json
import os

designs_dir = '/Users/muyaowu/Documents/PhrollerDesign/PhrollerDesigns/assets/designs'
files = [f for f in os.listdir(designs_dir) if f.endswith('.json')]

physics_keys = ['globalFriction', 'slidingDamping', 'globalBounciness', 'drag']

for filename in files:
    path = os.path.join(designs_dir, filename)
    print(f"Processing {filename}...")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Remove dice
    if 'preset' in data:
        print(f"  Removing 'preset' from {filename}")
        del data['preset']
    if 'arsenalDice' in data:
        print(f"  Removing 'arsenalDice' from {filename}")
        del data['arsenalDice']
    
    # Remove physics settings
    if 'settings' in data:
        for key in physics_keys:
            if key in data['settings']:
                print(f"  Removing 'settings.{key}' from {filename}")
                del data['settings'][key]
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

print("Done!")
