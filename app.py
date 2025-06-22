from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import time
import threading

app = Flask(__name__)

@app.route('/')
def index():
    saved_bitrate = request.cookies.get('bitrate', '192')  # Default to 192kbps
    return render_template('index.html', saved_bitrate=saved_bitrate)

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    bitrate = request.form['bitrate']

    output_folder = 'downloads'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate,
        }],
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        base_path = ydl.prepare_filename(info_dict)
        file_path, _ = os.path.splitext(base_path)
        file_path += '.mp3'

    @after_this_request
    def cleanup(response):
        def delete(path):
            time.sleep(1) 
            try:
                os.remove(path)
            except Exception as e:
                app.logger.error("Error removing or closing downloaded file handle: %s", e)
        threading.Thread(target=delete, args=(file_path,)).start()
        return response

    download_name = os.path.basename(file_path)
    response = send_file(
        file_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='audio/mpeg'
    )
    response.set_cookie('bitrate', bitrate)
    return response

if __name__ == '__main__':
    app.run(debug=True) 