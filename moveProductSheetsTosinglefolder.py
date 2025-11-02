import os
import shutil

def extract_files(source_root, destination_folder, file_extension, suffix):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    for product_dir in os.listdir(source_root):
        product_path = os.path.join(source_root, product_dir)
        if os.path.isdir(product_path):
            for file_name in os.listdir(product_path):
                if file_name.lower().endswith(file_extension):
                    source_file = os.path.join(product_path, file_name)
                    new_file_name = f"{product_dir}_{suffix}{file_extension}"
                    dest_file = os.path.join(destination_folder, new_file_name)
                    shutil.copy2(source_file, dest_file)
                    print(f"Copied {source_file} to {dest_file}")

# Example usage
source_folder = 'D:\Palak'  # Replace with your root folder containing product folders
destination_folder = 'D:\Palak\ProductSheets'  # Replace with your desired destination folder

# Extract all product sheets (PDF files)
extract_files(source_folder, destination_folder, '.pdf', 'productsheet')

# Extract all features text files
extract_files(source_folder, destination_folder, '.txt', 'features')
