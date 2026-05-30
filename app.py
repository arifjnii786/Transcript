import streamlit as st
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import concurrent.futures

# --- APP LAYOUT CONFIG ---
st.set_page_config(
    page_title="Shorts Transcript Hub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Elegant CSS for a pristine interface
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { font-weight: 800; color: #1E293B; letter-spacing: -0.5px; }
    .video-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .video-title {
        font-size: 16px;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 8px;
    }
    .badge-success {
        background-color: #DCFCE7;
        color: #14532D;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-failed {
        background-color: #FEE2E2;
        color: #7F1D1D;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    </style>
""", unsafe_html=True)


# --- DATA EXTRACTION BACKEND ---
def get_shorts_ids(channel_handle, max_results):
    if not channel_handle.startswith('@'):
        channel_handle = f"@{channel_handle}"
    url = f"https://www.youtube.com/{channel_handle}/shorts"
    ydl_opts = {
        'extract_flat': True,
        'playlistend': max_results,
        'quiet': True,
        'no_warnings': True
    }
    video_data = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' in result:
                for entry in result['entries']:
                    if entry:
                        video_data.append({
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': f"https://youtube.com/shorts/{entry.get('id')}"
                        })
    except Exception as e:
        st.error(f"Error communicating with YouTube: {e}")
    return video_data

def fetch_single_transcript(video):
    v_id = video['id']
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(v_id, languages=['en'])
        full_text = " ".join([chunk['text'] for chunk in transcript_list])
        return {**video, 'transcript': full_text, 'status': 'Success'}
    except (NoTranscriptFound, TranscriptsDisabled):
        return {**video, 'transcript': "[System Note: No English subtitles/transcript found for this video]", 'status': 'Failed'}
    except Exception as e:
        return {**video, 'transcript': f"[System Error: {str(e)}]", 'status': 'Error'}

def bulk_extract_transcripts(video_list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch_single_transcript, video_list))
    return results


# --- SIDEBAR INTERFACE ---
with st.sidebar:
    st.markdown("<h2 style='color:#0F172A; font-weight:700; margin-bottom:20px;'>🔧 Source Engine</h2>", unsafe_html=True)
    handle = st.text_input("Channel Handle", placeholder="@username")
    count = st.slider("Videos Target Count", min_value=1, max_value=30, value=5)
    
    st.markdown("<div style='margin-top:25px;'></div>", unsafe_html=True)
    submit_btn = st.button("⚡ Extract Transcripts", use_container_width=True, type="primary")


# --- MAIN SCREEN INTERFACE ---
st.markdown("<h1>🎬 YouTube Shorts Transcript Hub</h1>", unsafe_html=True)
st.markdown("<p style='color:#64748B; font-size:15px; margin-bottom:30px;'>Bulk extraction utility built for fast workflow optimization.</p>", unsafe_html=True)

if submit_btn:
    if not handle.strip():
        st.toast("⚠️ Please enter a valid channel handle first!", icon="⚠️")
    else:
        with st.spinner("🔍 Connecting to channel metrics and crawling video lists..."):
            shorts = get_shorts_ids(handle, count)
            
        if not shorts:
            st.error("No valid Shorts items discovered. Check handle spelling or connection settings.")
        else:
            with st.spinner(f"📥 Extracting text profiles for {len(shorts)} videos concurrently..."):
                extracted_data = bulk_extract_transcripts(shorts)
            
            st.toast("✨ Bulk data extraction finished!", icon="✅")
            
            compiled_text = ""
            successful_transcripts_count = 0
            
            for index, item in enumerate(extracted_data):
                if item['status'] == 'Success':
                    successful_transcripts_count += 1
                    compiled_text += f"TITLE: {item['title']}\nURL: {item['url']}\nTRANSCRIPT:\n{item['transcript']}\n\n"
                    compiled_text += "="*80 + "\n\n"
            
            st.markdown("### ⚡ Bulk Operations Action Bar")
            
            st.download_button(
                label="📥 Download ALL Transcripts (Single Text File)",
                data=compiled_text,
                file_name=f"{handle.replace('@','')}_all_transcripts.txt",
                mime="text/plain",
                use_container_width=True,
            )
            
            st.text_area("📋 Copy All Field (Select All -> Copy)", value=compiled_text, height=120, help="Click anywhere inside, press Ctrl+A then Ctrl+C to copy all instantly.")

            st.markdown("<hr style='border:0.5px solid #E2E8F0; margin: 30px 0;'>", unsafe_html=True)
            
            st.markdown(f"### 📂 Individual Item Profiles ({successful_transcripts_count} Extracted Successfully)")
            
            for index, item in enumerate(extracted_data):
                status_badge = f"<span class='badge-success'>✓ Success</span>" if item['status'] == 'Success' else f"<span class='badge-failed'>✗ {item['status']}</span>"
                
                st.markdown(f"""
                    <div class='video-card'>
                        <div class='video-title'>{item['title']}</div>
                        <div style='margin-bottom: 12px;'>{status_badge} &nbsp;|&nbsp; <a href='{item['url']}' target='_blank' style='color:#2563EB; font-size:13px; font-weight:500; text-decoration:none;'>🔗 View Original Short</a></div>
                    </div>
                """, unsafe_html=True)
                
                if item['status'] == 'Success':
                    st.text_area("Transcript Output", value=item['transcript'], height=110, key=f"individual_{index}", label_visibility="collapsed")
                else:
                    st.caption(f"Status notification: {item['transcript']}")
                
                st.markdown("<div style='margin-bottom:25px;'></div>", unsafe_html=True)
else:
    st.info("💡 Pro Tip: Enter a channel handle on the left control panel (e.g., `@MrBeast`) and click 'Extract Transcripts' to populate this canvas.")
