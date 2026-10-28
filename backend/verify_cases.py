import urllib.request, urllib.error, json, io, time
from PIL import Image

BASE = 'http://127.0.0.1:8000'

def post_file(filename, content, content_type='image/png'):
    boundary = '----WebKitFormBoundaryTestVerify7788'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: {content_type}\r\n\r\n'
    ).encode('latin-1') + content + f'\r\n--{boundary}--\r\n'.encode('latin-1')
    req = urllib.request.Request(
        f'{BASE}/api/analyze',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    t0 = time.perf_counter()
    try:
        res = urllib.request.urlopen(req)
        dt = (time.perf_counter() - t0) * 1000
        return res.status, json.loads(res.read().decode()), dt
    except urllib.error.HTTPError as e:
        dt = (time.perf_counter() - t0) * 1000
        return e.code, json.loads(e.read().decode()), dt

# 1. Valid X-ray (synthetic PNG)
img = Image.new('L', (512, 512), color=120)
buf = io.BytesIO()
img.save(buf, format='PNG')
status, data, dt = post_file('valid_normal_cxr.png', buf.getvalue(), 'image/png')
print(f'1. Valid X-ray: HTTP {status} in {dt:.1f}ms (isSimulated: {data.get("isSimulatedFallback")}, Top: {data.get("topFinding", {}).get("name")})')

# 1b. Genuine Chest Radiograph (sample_xray.png)
import os
for sample_path in ['sample_xray.png', '../sample_xray.png', 'backend/sample_xray.png', 'frontend/public/samples/sample_xray.png']:
    if os.path.exists(sample_path):
        with open(sample_path, 'rb') as f:
            real_bytes = f.read()
        status, data, dt = post_file('sample_xray.png', real_bytes, 'image/png')
        print(f'1b. Genuine X-Ray (sample_xray.png): HTTP {status} in {dt:.1f}ms (isSimulated: {data.get("isSimulatedFallback")}, Top: {data.get("topFinding", {}).get("name")}, Prob: {data.get("topFinding", {}).get("probability")})')
        break

# 1c. Clean Genuine Chest Radiograph (sample_xray_clean.png)
for clean_path in ['sample_xray_clean.png', '../sample_xray_clean.png', 'frontend/public/samples/sample_xray_clean.png']:
    if os.path.exists(clean_path):
        with open(clean_path, 'rb') as f:
            clean_bytes = f.read()
        status, data, dt = post_file('sample_xray_clean.png', clean_bytes, 'image/png')
        print(f'1c. Clean Genuine X-Ray (sample_xray_clean.png): HTTP {status} in {dt:.1f}ms (isSimulated: {data.get("isSimulatedFallback")}, Top: {data.get("topFinding", {}).get("name")}, Prob: {data.get("topFinding", {}).get("probability")})')
        break

# 2. Invalid image (text file masquerading as image)
status, data, dt = post_file('fake.png', b'This is just a text file with wrong bytes', 'image/png')
print(f'2. Invalid image (magic byte spoof): HTTP {status} detail: {data.get("detail")}')

# 3. Corrupted image (PNG header but corrupted body)
corrupted = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRcorruptedjunkdatahere'
status, data, dt = post_file('corrupted.png', corrupted, 'image/png')
print(f'3. Corrupted image: HTTP {status} detail: {data.get("detail")}')

# 4. Unsupported file (.exe)
status, data, dt = post_file('malware.exe', b'MZ\x90\x00binary', 'application/x-dosexec')
print(f'4. Unsupported file (.exe): HTTP {status} detail: {data.get("detail")}')

# 5. Oversized file (>10MB)
oversized = b'x' * (11 * 1024 * 1024)
status, data, dt = post_file('huge.png', oversized, 'image/png')
print(f'5. Oversized file (>10MB): HTTP {status} detail: {data.get("detail")}')

# 6. Zero-byte file
status, data, dt = post_file('zero.png', b'', 'image/png')
print(f'6. Zero-byte file: HTTP {status} detail: {data.get("detail")}')
