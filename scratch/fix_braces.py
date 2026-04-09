import re
import os

filepath = r'c:\Users\GOWRI SIMHA\rnsittrack2\devready\daemon\api\visualization.py'

if not os.path.exists(filepath):
    print(f"Error: File not found at {filepath}")
    exit(1)

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = []
in_fstring = False
fstring_start_idx = -1

for i, line in enumerate(lines):
    # Detect the start of the function and the f-string
    if 'async def visualize_team():' in line:
        fstring_start_idx = i
    
    if fstring_start_idx != -1 and 'html_content = f"""' in line:
        in_fstring = True
        output_lines.append(line)
        continue
    
    if in_fstring:
        # Check for the end of the f-string (return line or closing quotes)
        if '"""' in line and i > fstring_start_idx + 2:
            in_fstring = False
            output_lines.append(line)
            continue
        
        # Double single { and } while preserving already doubled ones
        # Placeholder for already doubled
        temp = line.replace('{{', '[[OPEN]]').replace('}}', '[[CLOSE]]')
        # Double remaining singles
        temp = temp.replace('{', '{{').replace('}', '}}')
        # Restore
        temp = temp.replace('[[OPEN]]', '{{').replace('[[CLOSE]]', '}}')
        
        output_lines.append(temp)
    else:
        output_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("Successfully processed visualization.py")
