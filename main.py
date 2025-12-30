import os
import uuid
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docxtpl import DocxTemplate

TEMPLATE_DIR = "/tmp/templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

app = FastAPI()

class RenderBody(BaseModel):
    template_id: str
    data: dict

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/templates")
async def upload_template(file: UploadFile = File(...), name: str = Form("template")):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="template must be .docx")

    template_id = str(uuid.uuid4())
    path = os.path.join(TEMPLATE_DIR, f"{template_id}.docx")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    with open(path, "wb") as f:
        f.write(content)

    return JSONResponse({"template_id": template_id, "name": name})

@app.post("/render")
def render_docx(body: RenderBody):
    path = os.path.join(TEMPLATE_DIR, f"{body.template_id}.docx")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="template_id not found")

    doc = DocxTemplate(path)
    doc.render(body.data)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    filename = "formatted.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
