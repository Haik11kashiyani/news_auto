from moviepy.editor import *
from moviepy.video.fx import all as vfx
import os
import random

class VideoEditor:
    def __init__(self):
        self.output_dir = "generated_videos"
        os.makedirs(self.output_dir, exist_ok=True)

    def assemble_video(self, bg_path, bg_type, overlay_path, audio_path, output_filename="final.mp4"):
        """
        Assembles: Background (Image/Video) + Overlay (Sequence/Image) + Audio
        """
        try:
            # 1. Output Path
            output_path = os.path.join(self.output_dir, output_filename)
            print(f"Assembling video: {output_path}")

            clips = []
            audio_clips = []

            # Ensure we are working with a list of segments
            segments = overlay_path if isinstance(overlay_path, list) else []
            if not segments and isinstance(overlay_path, str):
                # Legacy fallback
                segments = [{"image": overlay_path, "audio": audio_path}]

            print(f"Assembling {len(segments)} segments...")

            for i, seg in enumerate(segments):
                a_path = seg.get("audio") or audio_path
                i_path = seg.get("image")
                
                if not i_path: continue

                # A. AUDIO
                if a_path and os.path.exists(a_path):
                    ac = AudioFileClip(a_path)
                    seg_duration = ac.duration
                    audio_clips.append(ac)
                else:
                    seg_duration = 5 # Default
                
                # B. BACKGROUND (Per Segment)
                if not bg_path or not os.path.exists(bg_path):
                    # FALLBACK: Create a gradient background instead of pure black
                    print(f"[BG] No image found, creating gradient fallback...")
                    bg_clip = self._create_gradient_bg(seg_duration)
                elif bg_type == "video":
                    bg_clip = VideoFileClip(bg_path, audio=False)
                    # Loop/Cut
                    if bg_clip.duration < seg_duration:
                        bg_clip = vfx.loop(bg_clip, duration=seg_duration)
                    else:
                        bg_clip = bg_clip.subclip(0, seg_duration)
                    bg_clip = bg_clip.resize(height=1920).crop(x1=0, y1=0, width=1080, height=1920)
                else:
                    # Image BG: Viral Blur Style
                    bg_img_clip = ImageClip(bg_path).set_duration(seg_duration)
                    
                    # 1. Blurred Background
                    bg_blurred = bg_img_clip.resize(height=1920)
                    if bg_blurred.w < 1080: bg_blurred = bg_blurred.resize(width=1080)
                    bg_blurred = bg_blurred.crop(x1=0, y1=0, width=1080, height=1920).set_position("center")
                    bg_blurred = bg_blurred.resize(0.05).resize(20) # Blur trick

                    # 2. Sharp Image Foreground
                    fg_img_clip = ImageClip(bg_path).set_duration(seg_duration).resize(width=1080).set_position("center")
                    
                    bg_clip = CompositeVideoClip([bg_blurred, fg_img_clip], size=(1080,1920)).set_duration(seg_duration)

                # C. CARD OVERLAY
                # Static center card
                card_clip = ImageClip(i_path).set_duration(seg_duration).resize(newsize=(1080, 1920)).set_position("center")

                # D. TICKER (REMOVED REQUEST)
                # ticker_path = seg.get("ticker_image")
                layers = [bg_clip, card_clip]
                
                # if ticker_path and os.path.exists(ticker_path):
                #     ticker_img = ImageClip(ticker_path).set_duration(seg_duration)
                #     scroll_speed = 250
                #     ticker_y = 1750
                #     # Scroll Right to Left
                #     ticker_clip = ticker_img.set_position(lambda t: (1080 - int(scroll_speed * t), ticker_y))
                #     layers.append(ticker_clip)

                # COMPOSITE SEGMENT
                segment_comp = CompositeVideoClip(layers, size=(1080,1920)).set_duration(seg_duration)
                
                # Apply Crossfade to entrance of segments (except first)
                if i > 0:
                    segment_comp = segment_comp.crossfadein(0.5)
                
                clips.append(segment_comp)

            if not clips:
                print("No clips generated.")
                return None

            # 3. Concatenate (Method='compose' handles the crossfades)
            # padding=-0.5 allows overlapping for the crossfade duration
            # Note: For simple crossfadein, we might not strictly need padding if we just overlap opacity, 
            # but standard concat simply plays sequentially.
            # To get TRUE crossfade (clip A fading out valid clip B fading in), we need Composite or overlapping concat.
            # MoviePy v1 concat with padding is tricky.
            # Simpler approach: sequential play, but each clip starts with a fade-in (from black/previous).
            # This works visually as a "transition".
            
            final_video = concatenate_videoclips(clips, method="compose", padding=-0.5)
            
            # Rebuild Audio
            final_audio_track = concatenate_audioclips(audio_clips)
            final_video = final_video.set_audio(final_audio_track)

            # 4. Write Output
            os.makedirs(self.output_dir, exist_ok=True)
            
            final_video.write_videofile(
                output_path, 
                fps=24, 
                codec='libx264', 
                audio_codec='aac', 
                threads=1, 
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True
            )
            
            return output_path

        except Exception as e:
            print(f"Error editing video: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_gradient_bg(self, duration):
        """
        Creates a professional gradient background as fallback.
        Uses numpy to create a vertical gradient from dark blue to black.
        """
        import numpy as np
        
        width, height = 1080, 1920
        
        # Create gradient array (dark blue to black)
        gradient = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            # Dark blue at top, black at bottom
            ratio = y / height
            r = int(15 * (1 - ratio))  # Dark red component
            g = int(25 * (1 - ratio))  # Dark green component
            b = int(60 * (1 - ratio))  # Dark blue component
            gradient[y, :] = [r, g, b]
        
        # Create clip from array
        clip = ImageClip(gradient).set_duration(duration)
        return clip

if __name__ == "__main__":
    # Mock Test
    pass
