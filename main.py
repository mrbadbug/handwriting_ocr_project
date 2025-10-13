import os
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import easyocr
from docx import Document
import shutil
import uuid

app = FastAPI()

# Create uploads folder if not exist
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mount static folder for css/js if needed
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Initialize EasyOCR reader once (English only here)
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have GPU and CUDA


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload/")
async def upload_handwriting(file: UploadFile = File(...)):
    # Save the uploaded file
    file_extension = file.filename.split(".")[-1]
    if file_extension.lower() not in ("png", "jpg", "jpeg"):
        return {"error": "Unsupported file type"}

    temp_image_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.{file_extension}")
    with open(temp_image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Perform OCR using EasyOCR
    results = reader.readtext(temp_image_path, detail=0)  # detail=0 to get just text

    # Combine lines into paragraphs (simple join)
    recognized_text = "\n".join(results)

    # Create Word document
    doc = Document()
    doc.add_paragraph(recognized_text)

    output_docx_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.docx")
    doc.save(output_docx_path)

    # Clean up uploaded image file
    os.remove(temp_image_path)

    # Return the docx file for download
    return FileResponse(
        path=output_docx_path,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename="recognized_text.docx",
        background=lambda: os.remove(output_docx_path)  # Delete docx after sending
    )
