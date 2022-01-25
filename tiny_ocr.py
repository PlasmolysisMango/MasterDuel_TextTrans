import ctypes
from PIL import Image
DLL_PATH = './tesseract41.dll'
TESSDATA_PREFIX = b'./tessdata'
lang = b'eng'

tesseract = ctypes.cdll.LoadLibrary(DLL_PATH)
tesseract.TessBaseAPICreate.restype = ctypes.c_uint64
api = tesseract.TessBaseAPICreate()
tesseract.TessBaseAPISetVariable(ctypes.c_uint64(api), b'debug_file', b'/dev/null')
rc = tesseract.TessBaseAPIInit3(ctypes.c_uint64(api), TESSDATA_PREFIX, lang)
if rc:
    tesseract.TessBaseAPIDelete(ctypes.c_uint64(api))
    print('Could not initialize tesseract.\n')
    exit(3)

def file_to_string(path: str) -> str:
    path = path.encode('utf8')
    tesseract.TessBaseAPIProcessPages(
        ctypes.c_uint64(api), path, None, 0, None)
    tesseract.TessBaseAPIGetUTF8Text.restype = ctypes.c_uint64
    text_out = tesseract.TessBaseAPIGetUTF8Text(ctypes.c_uint64(api))
    return bytes.decode(ctypes.string_at(text_out)).strip()

if __name__ == '__main__':
    image_file_path = './tmp.png'
    result = file_to_string(image_file_path)
    print(result)