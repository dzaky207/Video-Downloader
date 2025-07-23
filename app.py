import streamlit as st
import yt_dlp
import os

st.title("Video Downloader")

video_url = st.text_input("Enter Video URL:")

formats_info = []
selected_video_format = None
audio_format_id = None

if video_url:
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get("formats", [])

            audio_formats = [
                f for f in formats
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none'
            ]
            if audio_formats:
                best_audio = max(audio_formats, key=lambda f: f.get('abr') or 0)
                audio_format_id = best_audio['format_id']

            video_formats = [
                f for f in formats
                if f.get('vcodec') != 'none' and f.get('acodec') == 'none'
            ]
            for f in video_formats:
                resolution = f.get('format_note') or f.get('height') or 'unknown'
                ext = f.get('ext', 'mp4')
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_mb = f"{round(filesize / 1024 / 1024, 2)} MB" if filesize else "Unknown size"
                formats_info.append({
                    'format_id': f['format_id'],
                    'desc': f"{resolution} - {ext} - {size_mb}"
                })

            if formats_info:
                selected = st.selectbox("Select video resolution:",
                                        formats_info,
                                        format_func=lambda x: x['desc'])
                selected_video_format = selected['format_id']

        except Exception as e:
            st.error(f"Failed to load video info: {e}")

download_clicked = st.button("Download")

progress_placeholder = st.empty()
status_placeholder = st.empty()

download_file = None
filename = ""

if download_clicked:
    if not video_url or not selected_video_format or not audio_format_id:
        st.warning("Please enter a URL and select resolution first.")
    else:
        progress_bar = progress_placeholder.progress(0)

        def progress_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)

                if total_bytes and downloaded_bytes:
                    progress = int(downloaded_bytes / total_bytes * 100)
                    progress_bar.progress(progress)
                    status_placeholder.info(f"Downloading... {progress}%")
                else:
                    status_placeholder.info("Downloading...")

            elif d['status'] == 'finished':
                progress_bar.progress(100)
                status_placeholder.success("Download complete, saving file...")

        ydl_opts = {
            'format': f"{selected_video_format}+{audio_format_id}",
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".mkv", ".mp4")
                if os.path.exists(filename):
                    with open(filename, "rb") as f:
                        download_file = f.read()
                    status_placeholder.success("Video downloaded successfully!")
            except Exception as e:
                status_placeholder.error(f"An error occurred while downloading: {e}")

if download_file and filename:
    st.download_button(label="Click to download file",
                       data=download_file,
                       file_name=os.path.basename(filename),
                       mime="video/mp4")
