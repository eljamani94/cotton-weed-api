# Streamlit Integration Guide

## Problem: 502 Errors When Calling API from Streamlit

The error you're seeing:
```
HTTPSConnectionPool(host='cotton-weed-api.onrender.com', port=443): Max retries exceeded with url: /predict (Caused by ResponseError('too many 502 error responses'))
```

This happens because:
1. The prediction takes time (model inference)
2. The request might be timing out
3. Memory issues on Render's free tier causing worker crashes

## Solution: Fix Your Streamlit App's API Calls

### 1. **Increase Timeout** in Streamlit App

Your Streamlit app needs to wait longer for predictions. Update your API call code:

```python
import requests
import streamlit as st

API_URL = "https://cotton-weed-api.onrender.com"

def predict_image(image_file):
    """Call the API to predict weeds in image"""
    try:
        # Prepare the file for upload
        files = {'file': ('image.jpg', image_file, 'image/jpeg')}

        # Make request with longer timeout (60 seconds)
        response = requests.post(
            f"{API_URL}/predict",
            files=files,
            timeout=60  # IMPORTANT: Increase from default (usually 10s)
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.Timeout:
        st.error("Request timed out. The API might be processing a large image or is under heavy load.")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: {e}")
        st.info("The API might be starting up. Try again in a minute.")
        return None
    except Exception as e:
        st.error(f"Error calling API: {e}")
        return None
```

### 2. **Add Retry Logic** (Optional but Recommended)

If Render.com is cold-starting (free tier sleeps after inactivity), add retry logic:

```python
import time

def predict_image_with_retry(image_file, max_retries=3):
    """Call API with retry logic"""
    for attempt in range(max_retries):
        try:
            files = {'file': ('image.jpg', image_file, 'image/jpeg')}

            response = requests.post(
                f"{API_URL}/predict",
                files=files,
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 502:
                if attempt < max_retries - 1:
                    st.warning(f"API is starting up... Retry {attempt + 1}/{max_retries}")
                    time.sleep(5)  # Wait 5 seconds before retry
                    continue
                else:
                    st.error("API is unavailable after multiple retries")
                    return None
            else:
                st.error(f"API Error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                st.warning(f"Timeout... Retry {attempt + 1}/{max_retries}")
                time.sleep(5)
                continue
            else:
                st.error("Request timed out after multiple retries")
                return None
        except Exception as e:
            st.error(f"Error: {e}")
            return None

    return None
```

### 3. **Resize Images Before Upload** (Important!)

Large images cause memory issues. Resize in Streamlit before sending:

```python
from PIL import Image
import io

def resize_image_for_api(image, max_size=1280):
    """Resize image to reduce API memory usage"""
    # Check if resize needed
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.LANCZOS)

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)

    return img_byte_arr

# Usage in your Streamlit app:
uploaded_file = st.file_uploader("Choose an image...")
if uploaded_file:
    image = Image.open(uploaded_file)

    # Resize before sending to API
    resized_image_bytes = resize_image_for_api(image)

    # Call API
    result = predict_image_with_retry(resized_image_bytes)
```

### 4. **Add Loading Indicator**

Show user the API is working:

```python
uploaded_file = st.file_uploader("Choose an image...")
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("Detect Weeds"):
        with st.spinner("Processing image... This may take up to 60 seconds..."):
            resized_image_bytes = resize_image_for_api(image)
            result = predict_image_with_retry(resized_image_bytes)

            if result:
                st.success(f"Found {result['num_detections']} weeds!")
                st.json(result)
```

### 5. **Health Check Before Upload** (Optional)

Check if API is alive before uploading:

```python
def check_api_health():
    """Check if API is healthy"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

# In your Streamlit app:
if st.button("Detect Weeds"):
    # Check API health first
    if not check_api_health():
        st.error("API is not responding. It might be starting up (this takes ~30 seconds on first request).")
        st.info("Please wait a moment and try again.")
    else:
        # Proceed with prediction
        with st.spinner("Processing..."):
            result = predict_image_with_retry(...)
```

## Complete Example for Streamlit App

```python
import streamlit as st
import requests
from PIL import Image
import io
import time

API_URL = "https://cotton-weed-api.onrender.com"

def resize_image_for_api(image, max_size=1280):
    """Resize image to reduce memory usage"""
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.LANCZOS)

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)
    return img_byte_arr

def predict_image(image_file, max_retries=2):
    """Call API with retry logic"""
    for attempt in range(max_retries):
        try:
            files = {'file': ('image.jpg', image_file, 'image/jpeg')}
            response = requests.post(
                f"{API_URL}/predict",
                files=files,
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 502 and attempt < max_retries - 1:
                st.warning(f"API warming up... Retry {attempt + 1}/{max_retries}")
                time.sleep(10)
                image_file.seek(0)  # Reset file pointer
                continue
            else:
                st.error(f"API Error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                st.warning("Request timed out, retrying...")
                time.sleep(5)
                image_file.seek(0)
                continue
            else:
                st.error("Request timed out")
                return None
        except Exception as e:
            st.error(f"Error: {e}")
            return None

    return None

# Streamlit UI
st.title("Cotton Weed Detection")

uploaded_file = st.file_uploader("Upload an image", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("Detect Weeds"):
        with st.spinner("Processing image... (up to 60 seconds)"):
            # Resize image
            resized_bytes = resize_image_for_api(image)

            # Call API
            result = predict_image(resized_bytes)

            if result:
                st.success(f"✓ Found {result['num_detections']} weed(s)!")

                # Display results
                if result['num_detections'] > 0:
                    st.write("### Detections:")
                    for i, (box, cls, conf) in enumerate(zip(
                        result['boxes'],
                        result['classes'],
                        result['confidences']
                    )):
                        st.write(f"{i+1}. {cls} - Confidence: {conf:.2%}")
```

## Testing Your Changes

1. Deploy the updated API code to Render.com
2. Wait for the deployment to complete (~2-5 minutes)
3. Test the API directly using the test script:
   ```bash
   python test_api.py path/to/test/image.jpg
   ```
4. If the test passes, update your Streamlit app with the code above
5. Deploy your updated Streamlit app

## Troubleshooting

### Still getting 502 errors?
- Check Render.com logs for error messages
- The free tier has memory limits (~512MB) - reduce workers to 1 (already done)
- Check if your model is too large for free tier

### Timeout errors?
- Increase timeout to 90 or 120 seconds
- Reduce image size before upload (max 1280px as shown above)
- Consider upgrading Render.com to paid tier for more resources

### Cold start issues?
- Render free tier spins down after 15 minutes of inactivity
- First request takes 30-60 seconds to wake up
- Add retry logic as shown above
- Consider upgrading to keep instance always running
