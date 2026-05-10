import os
import re

designs_dir = '/Users/muyaowu/Documents/PhrollerDesign/PhrollerDesigns/assets/designs'
files = [f for f in os.listdir(designs_dir) if f.endswith('.json')]

marker_start = re.compile(r'^<<<<<<< HEAD', re.MULTILINE)
marker_mid = re.compile(r'^=======', re.MULTILINE)
marker_end = re.compile(r'^>>>>>>> .*', re.MULTILINE)

def resolve_conflicts(content):
    lines = content.splitlines()
    new_lines = []
    in_conflict = False
    in_bad_side = False
    
    for line in lines:
        if marker_start.match(line):
            in_conflict = True
            in_bad_side = False
            continue
        if marker_mid.match(line):
            in_bad_side = True
            continue
        if marker_end.match(line):
            in_conflict = False
            in_bad_side = False
            continue
        
        if not in_bad_side:
            new_lines.append(line)
            
    return '\n'.join(new_lines)

for filename in files:
    path = os.path.join(designs_dir, filename)
    print(f"Resolving conflicts in {filename}...")
    
    with open(path, 'r') as f:
        content = f.read()
    
    resolved = resolve_conflicts(content)
    
    with open(path, 'w') as f:
        f.write(resolved)

print("Conflicts resolved. Now running physics cleanup...")

# Re-import and run the physics cleanup logic
import json
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
    with open(path, 'r') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"  Error loading {filename} after resolution: {e}")
            continue
    
    if 'settings' in data:
        for key in global_physics_keys:
            if key in data['settings']:
                del data['settings'][key]
    
    if 'preset' in data and data['preset'] is not None:
        groups = data['preset'].get('groups', [])
        for group in groups:
            if 'diceTypeData' in group:
                cleanup_dice_data(group['diceTypeData'])
    
    if 'arsenalDice' in data and data['arsenalDice'] is not None:
        for dice in data['arsenalDice']:
            cleanup_dice_data(dice)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

print("Done!")
