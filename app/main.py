from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response, HTMLResponse
import cv2
import tempfile
from pathlib import Path

app = FastAPI(title="Image Resizer")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image Resizer</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: #f4f7f9; 
            }
            h1 { color: #2c3e50; }
            .container { 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
            }
            input, button { 
                margin: 10px; 
                padding: 10px; 
                font-size: 16px; 
            }
            button { 
                background: #3498db; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
            }
            button:hover { background: #2980b9; }
            #result { margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖼️ Image Resizer</h1>
            <p><strong>Resize your image by any scale factor</strong></p>
            
            <input type="file" id="fileInput" accept="image/*">
            <br>
            <label>Scale Factor (e.g. 0.5 for half size, 0.33 for 1/3 size):</label><br>
            <input type="number" id="scaleInput" value="0.5" step="0.01" min="0.1" max="2.0">
            <br><br>
            <button onclick="resizeImage()">🔄 Resize Image</button>
            
            <div id="result"></div>
        </div>

        <script>
            async function resizeImage() {
                const fileInput = document.getElementById('fileInput');
                const scale = parseFloat(document.getElementById('scaleInput').value);
                const file = fileInput.files[0];
                
                if (!file) {
                    alert("Please select an image first!");
                    return;
                }
                if (isNaN(scale) || scale <= 0) {
                    alert("Please enter a valid scale factor (e.g. 0.5)");
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);
                formData.append('scale', scale);

                const response = await fetch('/resize', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    
                    document.getElementById('result').innerHTML = `
                        <h3>✅ Image Resized Successfully! (Scale: ${scale})</h3>
                        <img src="${url}" style="max-width: 100%; border: 2px solid #ddd; border-radius: 10px; margin: 15px 0;">
                        <br><br>
                        <a href="${url}" download="resized_image.png">
                            <button style="background: #27ae60;">⬇️ Download Resized Image</button>
                        </a>
                    `;
                } else {
                    alert("Error processing image. Please try again.");
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/resize")
async def resize_image(file: UploadFile = File(...), scale: float = Form(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="File must be an image")

    if scale <= 0 or scale > 5:
        raise HTTPException(400, detail="Scale factor must be between 0.1 and 5.0")

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        img = cv2.imread(tmp_path)
        if img is None:
            raise HTTPException(400, detail="Could not read image")

        height, width = img.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

        success, encoded = cv2.imencode('.png', resized)
        if not success:
            raise HTTPException(500, detail="Failed to process image")

        return Response(
            content=encoded.tobytes(),
            media_type="image/png"
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
