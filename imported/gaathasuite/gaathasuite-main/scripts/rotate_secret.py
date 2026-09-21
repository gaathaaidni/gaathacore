import os
import secrets
import shutil

def rotate_env(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    # Create backup before rotation
    shutil.copy(file_path, f"{file_path}.bak")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_key = secrets.token_urlsafe(64)
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith('SECRET_KEY='):
            new_lines.append(f"SECRET_KEY={new_key}\n")
            updated = True
        else:
            new_lines.append(line)
            
    if not updated:
        new_lines.append(f"SECRET_KEY={new_key}\n")

    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    print(f"🔄 Successfully rotated SECRET_KEY in {file_path}. Backup: {file_path}.bak")

if __name__ == '__main__':
    rotate_env('.env')