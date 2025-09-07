import os
import tempfile

from flask import Flask, request, send_file, render_template
from requests import get
import ffmpeg

app = Flask(__name__)

BASE_LINK = "https://lasvideoblobs1prod-highvol.b-cdn.net/vods/blobs1/"


def clip_video(blob, time, length=6):
    link = BASE_LINK + blob
    file = get(link + "/index.m3u8").text
    current_time = 0
    prev_time = 0
    first_time = None
    files = []
    lines = file.split("\n")
    for line in lines:
        if line.startswith("#EXTINF:"):
            prev_time = current_time
            current_time += float(line[len("#EXTINF:"):].split(",")[0])
        elif current_time > time and prev_time < time + length:
            if first_time is None:
                first_time = prev_time
            files.append(link + "/" + line)

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        for ts in files:
            f.write(f"file '{ts}'\n")
    list_filename = f.name
    start_time = time - first_time
    merged = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    try:
        (
            ffmpeg
            .input(list_filename,
                   format="concat",
                   safe=0,
                   ss=start_time,
                   t=length,
                   protocol_whitelist="file,crypto,data,https,tls,tcp")
            .output("output.mp4",
                    vcodec="libx264", acodec="aac",
                    preset="veryfast", crf=23, fflags="+genpts")
            .run(overwrite_output=True)
        )
    finally:
        os.remove(list_filename)
        if os.path.exists(merged):
            os.remove(merged)


@app.post('/clip')
def hello_world():  # put application's code here
    print(request.form)
    length = int(request.form.get('length', 6))
    time_code = int(request.form['timecode'])
    link = request.form['link'].split("/game/")[1]
    clip_video(link, time_code, length)
    return send_file("output.mp4")

@app.get('/')
def home():
    return render_template("/home.html")


if __name__ == '__main__':
    app.run()
