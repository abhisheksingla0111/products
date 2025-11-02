from bs4 import BeautifulSoup
import os

# Path to your root folder containing txt files
root_folder = "D:\Palak"

# List of filenames to exclude (just the filename, not full path)
exclude_files = ["errors.txt", "local.txt", "failures.txt"]

for dirpath, dirnames, filenames in os.walk(root_folder):
    for filename in filenames:
        if filename.endswith(".txt") and filename not in exclude_files:
            file_path = os.path.join(dirpath, filename)
            
            # Read the original file
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract headline
            output_lines = []
            headline = soup.find("h3")
            if headline:
                output_lines.append(headline.get_text().strip())
                output_lines.append("")  # blank line after headline

            # Extract list items
            list_items = soup.find_all("li")
            for li in list_items:
                output_lines.append(f"- {li.get_text().strip()}")

            # Join all lines with line breaks
            clean_text = "\n".join(output_lines)

            # Overwrite the original file with cleaned text
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(clean_text)

            print(f"Processed and updated: {file_path}")
        else:
            if filename.endswith(".txt"):
                print(f"Skipped (excluded): {os.path.join(dirpath, filename)}")
