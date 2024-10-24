import json
from PIL import Image
import base64
import io

# Function to compress the image
from PIL import Image, UnidentifiedImageError
import base64
import io

def payload_has_image(payload):
    for message in payload.get('messages', []):
        if isinstance(message.get('content'), list):
            for item in message['content']:
                if item['type'] == 'image_url':
                    return True
    return False

# Function to compress the image
def compress_image(base64_str, max_size_kb=100):
    try:
        # Decode the base64 string to get the image
        image_data = base64.b64decode(base64_str.split(',')[1])
        image = Image.open(io.BytesIO(image_data))

        # Convert image to RGB if it's not in a compatible mode for saving as JPEG
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")

        # Compress the image until it's less than max_size_kb
        compressed_image_data = io.BytesIO()
        quality = 85  # Start with a quality of 85%
        
        while True:
            compressed_image_data.seek(0)
            image.save(compressed_image_data, format='JPEG', quality=quality)
            size_kb = compressed_image_data.tell() / 1024
            if size_kb <= max_size_kb or quality <= 10:
                break
            
            quality -= 5  # Reduce quality by 5%

        # Return the base64 string of the compressed image
        compressed_image_base64 = base64.b64encode(compressed_image_data.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{compressed_image_base64}"

    except UnidentifiedImageError:
        print("Error: Unable to identify the image format.")
        return base64_str  # Return the original image if something goes wrong

    except Exception as e:
        print(f"Error: {e}")
        return base64_str  # Return the original image if something goes wrong

# Function to process the payload and retain only the latest image
def process_image_payload(payload):
    latest_image_index = -1
    
    # Traverse to find the latest image index
    for i, message in enumerate(payload.get('messages', [])):
        if isinstance(message.get('content'), list):
            for j, item in enumerate(message['content']):
                if item['type'] == 'image_url':
                    latest_image_index = (i, j)  # Keep track of the latest image location

    # Process the messages and keep only the latest image
    if latest_image_index != -1:
        processed_messages = []
        
        for i, message in enumerate(payload.get('messages', [])):
            if isinstance(message.get('content'), list):
                new_content = []
                for j, item in enumerate(message['content']):
                    if item['type'] == 'image_url' and (i, j) == latest_image_index:
                        # Compress the latest image if its size is greater than 100kb
                        image_url = item['image_url']['url']
                        compressed_image_url = compress_image(image_url)
                        item['image_url']['url'] = compressed_image_url
                        new_content.append(item)
                    elif item['type'] != 'image_url':
                        new_content.append(item)
                        
                message['content'] = new_content
            
            processed_messages.append(message)
        
        payload['messages'] = processed_messages
    return payload
