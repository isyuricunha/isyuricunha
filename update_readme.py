import requests
import json
import random

def download_json():
    FILE_ID  = '1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92'
    FILE_URL = f'https://drive.google.com/uc?id={FILE_ID}'
    
    response = requests.get(FILE_URL)
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
#### database administrator based in brazil.

i solve complex data management challenges by designing, implementing, and maintaining high-performance, scalable, and secure database solutions

**find me on the web:**<br>
[website](https://yuricunha.com), [quick links](https://links.yuricunha.com), [meeting with me](https://cal.com/isyuricunha)

**link with me:**<br>
[x/twitter](https://twitter.com/isyuricunha), [readcv](https://read.cv/isyuricunha), [mail](mailto:isyuricunha@duck.com), [boo](https://signup.boo.world/jejk), [spotify](https://open.spotify.com/user/22wrcoowop6hb63heywvtaypy?si=e1e818483a1a43a1)

**last two blog post:**<br>
[One month after leaving the internet and leaving everyone believing I'm still active
](https://yuricunha.com/blog/one-month-after-leaving-the-internet-and-leaving-everyone-believing-im-still-active) and [My last goodbye](https://yuricunha.com/blog/my-last-goodbye)

**podcast and last ep:**<br>
[yuri cunha - blog speech](https://open.spotify.com/show/2XRQ2mpUbtT0ZqxFVrl0KK) and [trabalho, viagens, culturas e decisões](https://open.spotify.com/episode/4iqTnRWh5BC9Qy57h9CNGV?si=d38cf151deec4d47)

**a sentence to brighten your day:**<br>
    {line}

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
    main();
