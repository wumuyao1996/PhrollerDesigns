import os
import PIL.Image as Image
import shutil

# Configuration
IMAGE_DIR = 'assets/images'
MIN_SIZE_KB = 600
TARGET_RANGE = (500 * 1024, 600 * 1024)

def compress_image(source_path, target_range, original_ext):
    """
    Compresses an image to fall within the target size range in bytes.
    """
    img = Image.open(source_path)
    if img.mode == 'RGBA' and original_ext.lower() in ['.jpg', '.jpeg']:
        img = img.convert('RGB')
        
    temp_path = source_path + ".temp"
    
    if original_ext.lower() in ['.jpg', '.jpeg']:
        # For JPEG, adjust quality
        quality = 95
        last_size = float('inf')
        while quality > 5:
            img.save(temp_path, format='JPEG', quality=quality, optimize=True)
            size = os.path.getsize(temp_path)
            if size <= target_range[1]:
                if size >= target_range[0] or quality < 10:
                    break
            if size == last_size: # Avoid infinite loop if size doesn't change
                break
            last_size = size
            quality -= 5
    else:
        # For PNG, GIF and others, we'll try resizing
        width, height = img.size
        scale = 0.95
        last_size = float('inf')
        
        save_format = 'PNG'
        if original_ext.lower() == '.gif':
            save_format = 'GIF'
        elif original_ext.lower() == '.webp':
            save_format = 'WEBP'
        elif original_ext.lower() == '.bmp':
            save_format = 'BMP'

        while scale > 0.05:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            if save_format == 'GIF':
                # Simplified GIF handling (might lose animation frames)
                resized_img.save(temp_path, format=save_format)
            else:
                resized_img.save(temp_path, format=save_format, optimize=True)
                
            size = os.path.getsize(temp_path)
            if size <= target_range[1]:
                break
            
            if size >= last_size and scale < 0.9:
                scale *= 0.8
            else:
                scale -= 0.05
            last_size = size

    return temp_path

def main():
    abs_image_dir = os.path.abspath(IMAGE_DIR)
    if not os.path.exists(abs_image_dir):
        print(f"Directory {abs_image_dir} not found.")
        return

    files_processed = 0
    for filename in os.listdir(abs_image_dir):
        if '_raw' in filename:
            continue
            
        file_path = os.path.join(abs_image_dir, filename)
        if not os.path.isfile(file_path):
            continue
            
        # Check if it's an image
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']:
            continue

        size_bytes = os.path.getsize(file_path)
        size_kb = size_bytes / 1024
        
        if size_kb > MIN_SIZE_KB:
            print(f"Processing {filename} ({size_kb:.2f} KB)...")
            
            # 1. Rename original to _raw
            base, ext = os.path.splitext(filename)
            raw_filename = f"{base}_raw{ext}"
            raw_path = os.path.join(abs_image_dir, raw_filename)
            
            if os.path.exists(raw_path):
                print(f"  Raw file {raw_filename} already exists, using it as source.")
                source_path = raw_path
            else:
                shutil.move(file_path, raw_path)
                source_path = raw_path
            
            # 2. Compress
            try:
                compressed_temp = compress_image(source_path, TARGET_RANGE, ext)
                
                # 3. Save as original filename
                shutil.move(compressed_temp, file_path)
                new_size_kb = os.path.getsize(file_path) / 1024
                print(f"  Compressed {filename} to {new_size_kb:.2f} KB")
                files_processed += 1
            except Exception as e:
                print(f"  Error processing {filename}: {e}")
                # Restore original if failed and not already exists
                if not os.path.exists(file_path) and os.path.exists(source_path):
                    shutil.copy(source_path, file_path)

    if files_processed == 0:
        print("No images over 4MB found to compress.")
    else:
        print(f"Done. Processed {files_processed} images.")

if __name__ == "__main__":
    main()
