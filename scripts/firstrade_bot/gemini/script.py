from google import genai
from PIL import Image
from dotenv import load_dotenv
import os

# --- Configuration ---
# 1. Load environment variables from .env file
load_dotenv()

# 2. Get the API Key (optional check, as client handles it, but good practice)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment or .env file.")

# Define your image path
# --- **CHANGE THIS PATH** ---
image_path = os.getenv("IMAGE_PATH")
if not image_path:
    raise ValueError("IMAGE_PATH not found in environment or .env file.")
# -----------------------------

# --- Main Function ---

def analyze_image_with_gemini(image_path, prompt):
    """
    Loads an image, sends it to the Gemini model with a text prompt, 
    and prints the response.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return

    try:
        # The client will now automatically pick up the key from os.environ
        client = genai.Client() 

        # 1. Load the image using Pillow (PIL)
        print(f"Loading image from: {image_path}...")
        image = Image.open(image_path)
        
        # 2. Prepare the Multimodal Content
        content_parts = [
            image,  # The model automatically handles the PIL Image object
            prompt  # The text instruction
        ]

        # 3. Call the API
        print("Sending content to Gemini...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=content_parts
        )

        # 4. Print the Result
        print("\n--- Model Response ---")
        print(response.text)
        print("----------------------\n")
        return response.text

    except Exception as e:
        print(f"An error occurred: {e}")

# --- Execution ---
if __name__ == "__main__":
    # Define the question you want the model to answer about the image
    ANALYSIS_PROMPT = "understand the picture and convert to an excel sheet, return the csv content only without any other message"
    model_output_variable = analyze_image_with_gemini(image_path, ANALYSIS_PROMPT)
    print("XXXXX")
    print(model_output_variable)
    if model_output_variable:
        # You can now use 'model_output_variable' anywhere in your script
        print("\n--- Content Saved to Variable ---")
        print(f"Length of content saved: {len(model_output_variable)} characters")
        print("---------------------------------")
        # Example of using the variable: saving to a file
        output_filename = "image_analysis_output.txt"
        with open(output_filename, "w") as f:
            f.write(model_output_variable)
        print(f"Content successfully saved to {output_filename}")
