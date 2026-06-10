import re

def patch():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Insert <script src="data.js"></script> before <script>
    if '<script src="data.js"></script>' not in content:
        content = content.replace('<script>', '<script src="data.js"></script>\n    <script>')
        
    # Remove the massive const rawData = [...] line
    content = re.sub(r'const rawData = \[.*?\];', '// rawData is now loaded from data.js', content, count=1, flags=re.DOTALL)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    patch()
