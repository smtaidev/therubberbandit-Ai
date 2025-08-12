from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
from .extract import extract_text_sync
from .extract_schema import  ExtractResponse
from App.core.config import settings
from google.cloud import documentai
from google.oauth2 import service_account



router = APIRouter(prefix="/extraction", tags=["Extraction"])

credentials = service_account.Credentials.from_service_account_file(
settings.gcp_key_path
)
client = documentai.DocumentProcessorServiceClient(credentials=credentials)
PROCESSOR_NAME = (
    f"projects/{settings.gcp_project_id}/locations/{settings.gcp_location}/processors/{settings.gcp_processor_id}"
)

def get_text_from_text_anchor(document_text, text_anchor):
    if not text_anchor or not text_anchor.text_segments:
        return ""
    segment = text_anchor.text_segments[0]
    start = segment.start_index or 0
    end = segment.end_index or 0
    return document_text[start:end]


@router.post("/upload", response_model=ExtractResponse)
async def upload_and_extract(file: UploadFile = File(...)):
    mime_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    ext = "." + file.filename.lower().rsplit(".", 1)[-1]
    mime_type = mime_map.get(ext)
    if not mime_type:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, PNG, JPEG, or TIFF."
        )

    contents = await file.read()
    raw_doc = documentai.RawDocument(content=contents, mime_type=mime_type)

    try:
            request = documentai.ProcessRequest(
                name=PROCESSOR_NAME, raw_document=raw_doc
            )
            result = client.process_document(request=request)
            document = result.document

            form_fields = []
            for page in document.pages:
                for field in page.form_fields:
                    field_name = get_text_from_text_anchor(document.text, field.field_name.text_anchor).strip()
                    field_value = get_text_from_text_anchor(document.text, field.field_value.text_anchor).strip()

                    form_fields.append({
                        "name": field_name,
                        "value": field_value,
                        "confidence": field.field_value.confidence,
                    })

            return ExtractResponse(
                text=document.text,
                form_fields=form_fields
            )
    except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
