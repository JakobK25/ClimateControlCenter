import os
import glob

def fix_js_comments(directory):
    """Recursively find and fix JavaScript-style comments in all files."""
    # Get all files in directory and subdirectories
    file_types = ['*.py', '*.toml', '*.yml', '*.md', '*.env', '*.txt', '.env']
    
    fixed_count = 0
    
    for file_type in file_types:
        for filepath in glob.glob(os.path.join(directory, '**', file_type), recursive=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if the file starts with JavaScript comment
                if content.strip().startswith('// filepath:'):
                    # Remove the first line with the JavaScript comment
                    content = '\n'.join(content.split('\n')[1:])
                    
                    # Write the updated content back
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"Fixed: {filepath}")
                    fixed_count += 1
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
    
    return fixed_count

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    count = fix_js_comments(project_dir)
    print(f"\nFixed {count} files with JavaScript-style comments.")
    print("Done! Please restart your application.")