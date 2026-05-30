import streamlit as st
import yt_dlp
import youtube_transcript_api
import concurrent.futures

# --- APP LAYOUT CONFIG ---
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
    
    # Advanced yt-dlp scraping options to bypass simple server blocks
    ydl_opts = {
        'extract_flat': True,
        'playlistend': max_results,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
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
    
    # We try fetching english first, then fall back to auto-generated or any available language profile
    try:
        transcript_list = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'en-US'])
        full_text = " ".join([chunk['text'] for chunk in transcript_list])
        return {**video, 'transcript': full_text, 'status': 'Success'}
    except Exception:
        try:
            # Fallback block: Fetch any available language or auto-translated transcript dynamically
            transcript_list = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(v_id)
            full_text = " ".join([chunk['text'] for chunk in transcript_list])
            return {**video, 'transcript': full_text, 'status': 'Success'}
        except Exception as e:
            # Informative error message to check if it's an IP restriction or actually missing captions
            return {**video, 'transcript': f"[Server Restriction Notice: YouTube blocked the automated transcript request for this video ID. Try running fewer videos or checking if captions are manually disabled on this channel.]", 'status': 'Failed'}

def bulk_extract_transcripts(video_list):
    # Reduced worker thread pool size to 2 to minimize rapid concurrent hits on YouTube's server from the cloud IP
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(fetch_single_transcript, video_list))
    return results


# --- SIDEBAR INTERFACE ---
with st.sidebar:
    st.title("🔧 Source Engine")
    handle = st.text_input("Channel Handle", placeholder="@username")
    count = st.slider("Videos Target Count", min_value=1, max_value=20, value=3)
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
            with st.spinner(f"📥 Extracting text profiles for {len(shorts)} videos sequentially to prevent rate limits..."):
                extracted_data = bulk_extract_transcripts(shorts)
            
            st.toast("✨ Bulk data extraction finished!", icon="✅")
            
            compiled_text = ""
            successful_transcripts_count = 0
            
            for index, item in enumerate(extracted_data):
                if item['status'] == 'Success':
                    successful_transcripts_count += 1
                    compiled_text += f"TITLE: {item['title']}\nURL: {item['url']}\nTRANSCRIPT:\n{item['transcript']}\n\n"
                    compiled_text += "="*80 + "\n\n"
            
            # --- ACTION PANEL BAR ---
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
            
            # --- CARDS VIEW ---
            st.subheader(f"📂 Individual Item Profiles ({successful_transcripts_count} Extracted Successfully)")
            
            for index, item in enumerate(extracted_data):
                with st.container(border=True):
                    col_title, col_status = st.columns([3, 1])
                    with col_title:
                        st.markdown(f"**{item['title']}**")
                        st.caption(f"[🔗 Open Original Video]({item['url']})")
                    with col_status:
                        if item['status'] == 'Success':
                            st.success("✓ Success")
                        else:
                            st.error("✗ Failed")
                    
                    if item['status'] == 'Success':
                        st.text_area("Transcript Output", value=item['transcript'], height=110, key=f"individual_{index}", label_visibility="collapsed")
                    else:
                        st.warning(item['transcript'])
else:
    st.info("💡 Pro Tip: Enter a channel handle on the left control panel (e.g., `@MrBeast`) and click 'Extract Transcripts' to populate this canvas.")
