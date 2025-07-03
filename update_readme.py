import requests
import json
import random

def download_json():
    file_id  = '1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92'
    file_url = f'https://drive.google.com/uc?id={file_id}'
    
    response = requests.get(file_url)
    with open('./quotes.json', 'wb') as quotes_file:
        quotes_file.write(response.content)

def read_lines_from_json():
    with open('./quotes.json', 'r', encoding="utf-8") as quotes_file:
        quotes = json.load(quotes_file)
    
    lines = []
    for quote in quotes:
        for line in quote.get("lines"):
            lines.append(line)
    
    return lines

def generate_markdown_sentence(line):
    return f'''
**database administrator**

i manage, configure, and optimize databases and data systems to ensure high availability, data integrity, and optimal performance. i develop effective backup, recovery, and security strategies to protect critical information.

**find me on the web:**<br>
[personal website](https://yuricunha.com/?utm_source=github.com) | [quick links](https://links.yuricunha.com)

**connect with me:**<br>
- [x/twitter](https://twitter.com/isyuricunha)  
- [email (personal)](mailto:me@yuricunha.com)  
- [email (work)](mailto:contact@yuricunha.com)  
- [spotify](https://open.spotify.com/user/22wrcoowop6hb63heywvtaypy?si=e1e818483a1a43a1)

**blogs:**<br>
- [website blog](https://yuricunha.com/blog/?utm_source=github.com)  
- [bear blog](https://yuricunha.bearblog.dev/)

**a sentence to brighten your day:**<br>
    {line}

---

- Use of the code or derived products in videos, streaming, or similar public media is permitted with proper credit to the Author.  
- Modification, redistribution, or claiming original authorship without attribution is strictly forbidden.  
- Use of the code, in any form or derivative, for AI training, machine learning, or any artificial intelligence development is expressly prohibited.

'''

def write_readme(text):
    with open("./README.md", "w", encoding='utf8') as readme_file:
        readme_file.write(text)

def main():
    download_json()
    
    lines = read_lines_from_json()
    line = random.choice(lines)
    
    markdown_sentence = generate_markdown_sentence(line)
    write_readme(markdown_sentence)

if __name__ == "__main__":
    main()
