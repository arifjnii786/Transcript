import streamlit as st
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import concurrent.futures

# --- APP LAYOUT CONFIG (100% NATIVE) ---
st.set_page_config(
    page_title="Shorts Transcript Hub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.title("🔧 Source Engine")
    handle = st.text_input("Channel Handle", placeholder="@username")
    count = st.slider("Videos Target Count", min_value=1, max_value=30, value=5)
    submit_btn = st.button("⚡ Extract Transcripts", use_container_width=True, type="primary")


# --- MAIN SCREEN INTERFACE ---
st.title("🎬 YouTube Shorts Transcript Hub")
st.caption("Bulk extraction utility built for fast workflow optimization.")

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
            
            # Text Processing compiler
            compiled_text = ""
            successful_transcripts_count = 0
            
            for index, item in enumerate(extracted_data):
                if item['status'] == 'Success':
                    successful_transcripts_count += 1
                    compiled_text += f"TITLE: {item['title']}\nURL: {item['url']}\nTRANSCRIPT:\n{item['transcript']}\n\n"
                    compiled_text += "="*80 + "\n\n"
            
            # --- ACTION PANEL BAR (Native Columns) ---
            st.subheader("⚡ Bulk Operations Action Bar")
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Download ALL Transcripts (Single Text File)",
                    data=compiled_text,
                    file_name=f"{handle.replace('@','')}_all_transcripts.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col2:
                st.info("💡 Tip: Click inside the box below, press Ctrl+A then Ctrl+C to copy everything instantly.")
            
            st.text_area("📋 Unified Clipboard Backup (All Combined)", value=compiled_text, height=150)

            st.divider()
            
            # --- CHRONOLOGICAL NATIVE CARDS VIEW ---
            st.subheader(f"📂 Individual Item Profiles ({successful_transcripts_count} Extracted Successfully)")
            
            for index, item in enumerate(extracted_data):
                # Using Native Containers as modern cards
                with st.container(border=True):
                    col_title, col_status = st.columns([3, 1])
                    with col_title:
                        st.markdown(f"**{item['title']}**")
                        st.caption(f"[🔗 Open Original Video]({item['url']})")
                    with col_status:
                        if item['status'] == 'Success':
                            st.success("✓ Success")
                        else:
                            st.error(f"✗ {item['status']}")
                    
                    if item['status'] == 'Success':
                        st.text_area("Transcript Output", value=item['transcript'], height=110, key=f"individual_{index}", label_visibility="collapsed")
                    else:
                        st.warning(item['transcript'])
else:
    st.info("💡 Pro Tip: Enter a channel handle on the left control panel (e.g., `@MrBeast`) and click 'Extract Transcripts' to populate this canvas.")
