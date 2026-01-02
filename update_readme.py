import requests
import json
import random
import os
import sys

# default google drive file id for quotes
DEFAULT_FILE_ID = '1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92'


def download_json():
    """
    downloads the quotes json file from google drive.
    uses QUOTES_FILE_ID env var if set, otherwise uses default.
    """
    file_id = os.getenv('QUOTES_FILE_ID', DEFAULT_FILE_ID)
    file_url = f'https://drive.google.com/uc?id={file_id}'

    print(f"downloading quotes from google drive...")

    try:
        response = requests.get(file_url, timeout=10)
        response.raise_for_status()

        with open('./quotes.json', 'wb') as quotes_file:
            quotes_file.write(response.content)

        print("quotes downloaded successfully")

    except requests.exceptions.Timeout:
        print("error: request timed out while downloading quotes")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"error: failed to download quotes - {e}")
        sys.exit(1)
    except IOError as e:
        print(f"error: failed to save quotes file - {e}")
        sys.exit(1)


def read_lines_from_json():
    """
    reads and extracts all lines from the quotes json file.
    returns a flat list of all quote lines.
    """
    print("reading quotes from file...")

    try:
        with open('./quotes.json', 'r', encoding="utf-8") as quotes_file:
            quotes = json.load(quotes_file)

        # flatten all lines from all quotes into a single list
        lines = []
        for quote in quotes:
            for line in quote.get("lines", []):
                lines.append(line)

        if not lines:
            print("warning: no quotes found in file")
            return ["no quote available today"]

        print(f"found {len(lines)} quotes")
        return lines

    except FileNotFoundError:
        print("error: quotes.json file not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"error: invalid json format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"error: unexpected error reading quotes - {e}")
        sys.exit(1)


def generate_markdown_sentence(line):
    """
    generates the complete readme markdown content with the given quote line.
    """
    return f'''
**database administrator**

i manage, configure, and optimize databases and data systems to ensure high availability, data integrity, and optimal performance. i develop effective backup, recovery, and security strategies to protect critical information.

**find me on the web:**<br>
[personal website](https://yuricunha.com/?utm_source=github.com) | [quick links](https://links.yuricunha.com)

**connect with me:**<br>
- [x/twitter](https://x.com/isyuricunha)  
- [email (personal)](mailto:me@yuricunha.com)  
- [email (work)](mailto:contact@yuricunha.com)  
- [spotify](https://open.spotify.com/user/22wrcoowop6hb63heywvtaypy?si=e1e818483a1a43a1)

**blogs:**<br>
- [website blog](https://yuricunha.com/blog/?utm_source=github.com)  
- [bear blog](https://yuricunha.bearblog.dev/)

so you know, i am trying to get used to conventional commits, it is a bit annoying, actually


**a sentence to brighten your day:**<br>
    {line}

'''


def write_readme(text):
    """
    writes the generated markdown content to the readme file.
    """
    print("updating readme...")

    try:
        with open("./README.md", "w", encoding='utf8') as readme_file:
            readme_file.write(text)

        print("readme updated successfully")

    except IOError as e:
        print(f"error: failed to write readme file - {e}")
        sys.exit(1)


def main():
    """
    main function that orchestrates the readme update process.
    downloads quotes, picks a random one, and updates the readme.
    """
    print("starting readme update process...")

    # download the quotes file from google drive
    download_json()

    # read all quotes and pick a random one
    lines = read_lines_from_json()
    line = random.choice(lines)

    print(f"selected quote: {line[:50]}..." if len(
        line) > 50 else f"selected quote: {line}")

    # generate the full readme content
    markdown_sentence = generate_markdown_sentence(line)

    # write to readme file
    write_readme(markdown_sentence)

    print("all done!")


if __name__ == "__main__":
    main()
