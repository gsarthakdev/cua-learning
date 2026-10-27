import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from exceptions import EvaluationError
# EXPECTED = "Hello from my Python computer-use executor!"

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}

# DOCUMENT = Path.home() / "cua-learning/outputs/first-task.odt"

# Since we will run evaluator.py from run_task.py, we can simply pass in the PATH of the .odt file from run_task.py

def evaluate(task_name, document_path: Path, expected):
    """
    Args:
        task_name (str): Client defined name of the task.
        document_path (pathlib.PosixPath): The document's path, as a Path object.
        expected (str): The expected text/string to be found in the document.
    
    Returns:
        result (dict): Dictionary containing task_name, file_exists, content_matches, and success.
    """
    
    EXPECTED = expected
    DOCUMENT = document_path

    try:
        result = {
            "task_name": task_name,
            "file_exists": DOCUMENT.is_file(),
            "content_matches": False,
            "success": False # if content_matches==True, success=True
        }
        if not DOCUMENT.is_file():
            raise FileNotFoundError(f"Missing {DOCUMENT}")
        
        if not zipfile.is_zipfile(DOCUMENT):
            raise ValueError("Output is not a valid ODT ZIP archive")
        
        with zipfile.ZipFile(DOCUMENT) as archive:
            if archive.testzip() is not None:
                raise ValueError("ODT archive contains a corrupted member")
            
            xml_content = archive.read("content.xml")
        root = ET.fromstring(xml_content)
        # document_text = "".join(root.itertext())
        paragraphs = [
            "".join(p.itertext())
            for p in root.findall(
                ".//office:body/office:text//text:p", NS
            )
        ]
        
        # This task requires exactly one paragraph 
        result["content_matches"] = paragraphs == [EXPECTED]
        result["success"] = result["content_matches"]
        
    except Exception as error:
        result["error"] = str(error)
        raise EvaluationError(str(error), document_path) from error
    
    return result

    # print(json.dumps(result, indent=2))
    # sys.exit(0 if result["success"] else 1)
    