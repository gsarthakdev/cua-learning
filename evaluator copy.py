import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

message = "Hello from my Python computer-use executor!"
EXPECTED = message
DOCUMENT = Path.home() / "cua-learning/outputs/first-task.odt"

result = {
    "task": "Create Writer document",
    "file_exists": DOCUMENT.is_file(),
    "content_matches": False,
    "success": False
}

try:
    if not DOCUMENT.is_file():
        raise FileNotFoundError(f"Missing {DOCUMENT}")
    
    if not zipfile.is_zipfile(DOCUMENT):
        raise ValueError("Output is not a valid ODT ZIP archive")
    
    with zipfile.ZipFile(DOCUMENT) as archive:
        if archive.testzip() is not None:
            raise ValueError("ODT archive contains a corrupted member")
        
        content = archive.read("content.xml")
    root = ET.fromstring(content)
    document_text = "".join(root.itertext())
    
    result["content_matches"] = EXPECTED in document_text
    result["success"] = result["content_matches"]
    
except Exception as error:
    result["error"] = str(error)

print(json.dumps(result, indent=2))
sys.exit(0 if result["success"] else 1)