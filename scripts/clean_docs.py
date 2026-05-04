import re

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    
    c = re.sub(r'"evaluation_inputs".*?\n', '', c)
    c = re.sub(r'"evaluation_rules".*?\n', '', c)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)

clean_file('README.md')
clean_file('REVIEW_PACKET.md')
print("Cleaned!")
