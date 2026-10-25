"""Sample the studio's real renderer into a captioned MP4 (optional dev tool)."""
from __future__ import annotations
import argparse, base64, hashlib, json, os, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright
from verification import atomic_json, temporary_video, verified_response_sha

HERE = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--fps', type=int, default=12, choices=range(1, 61))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    target = a.out / 'PROMETHEUS-KITTY-GUIDED-DEMO.mp4'
    started = time.monotonic()
    errors = []
    with temporary_video(target) as pending:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
            try:
                page = browser.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1)
                page.on('pageerror', lambda e: errors.append(str(e)))
                document = page.context.request.get(a.url)
                served_sha = verified_response_sha(document, a.out / 'PROMETHEUS-MISSION-STUDIO.html')
                # Replay these verified server bytes exactly; large response bodies
                # may otherwise be evicted from Chromium's inspector cache.
                page.route(a.url, lambda route: route.fulfill(response=document))
                page.goto(a.url, wait_until='load')
                page.wait_for_function('PrometheusStudio.state.ready')
                page.locator('#quality').select_option('1')
                page.evaluate('PrometheusStudio.beginCapture(1920)')
                command = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', str(a.fps), '-i', 'pipe:0', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(pending)]
                process = subprocess.Popen(command, stdin=subprocess.PIPE)
                try:
                    for frame in range(132 * a.fps + 1):
                        t = min(132, frame / a.fps)
                        data = page.evaluate('(t)=>PrometheusStudio.advanceCapture(t)', t)
                        process.stdin.write(base64.b64decode(data.split(',', 1)[1]))
                        if frame % (a.fps * 8) == 0:
                            print(f'Rendered {t:.0f}/132 seconds', flush=True)
                    process.stdin.close()
                    code = process.wait(timeout=60)
                    if code:
                        raise RuntimeError('ffmpeg exited ' + str(code))
                finally:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=10)
            finally:
                browser.close()
        if errors:
            raise RuntimeError(str(errors))
        info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(pending)], text=True))
        stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
        assert stream['width'] == 1920 and stream['height'] == 1080
        assert float(info['format']['duration']) >= 132
        digest = hashlib.sha256(pending.read_bytes()).hexdigest()
        result = {'evidence_kind': 'MP4 sampled from the actual software simulation renderer; silent, no physical footage', 'fps': a.fps, 'width': 1920, 'height': 1080, 'duration_s': float(info['format']['duration']), 'frames': int(stream.get('nb_frames', 0)), 'bytes': pending.stat().st_size, 'sha256': digest, 'artifact_sha256': {target.name: digest}, 'html_sha256': served_sha, 'served_html_sha256': served_sha, 'input_sha256': {n: hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['render_video.py', 'verification.py']}, 'page_errors': errors, 'render_wall_s': round(time.monotonic()-started, 1)}
        # Failed rendering/probing leaves both the old video and record untouched.
        # A crash between replacements is detected by artifact_sha256 at packaging.
        os.replace(pending, target)
        atomic_json(a.out / 'VIDEO-VERIFICATION.json', result)
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
