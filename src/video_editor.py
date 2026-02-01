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
                else:
                    # Image BG: Premium Ken Burns (GSAP-style easing)
                    print(f"Applying Ken Burns to segment {i}...")
                    
                    # Load raw image
                    try:
                        raw_clip = ImageClip(bg_path).set_duration(seg_duration)
                        # Apply sophisticated Zoom/Pan
                        bg_clip = self.apply_ken_burns(raw_clip, seg_duration)
                        
                        # Add darkening layer (30% opacity) to ensure overlay text pops
                        dark_layer = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.3).set_duration(seg_duration)
                        bg_clip = CompositeVideoClip([bg_clip, dark_layer], size=(1080,1920))
                        
                    except Exception as e:
                        print(f"Ken Burns failed: {e}. Falling back to static.")
                        bg_clip = ImageClip(bg_path).set_duration(seg_duration).resize(height=1920).crop(x1=0, y1=0, width=1080, height=1920)

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
        Creates an ANIMATED gradient background as fallback.
        3-color gradient: White (30%), Dark color, Lighter version
        With subtle animation (color shift) + blur effect
        """
        import numpy as np
        from scipy.ndimage import gaussian_filter
        
        width, height = 1080, 1920
        
        # Define color stops (RGB)
        # White -> Dark Purple -> Light Purple (3 zones)
        color_white = np.array([255, 255, 255])  # 30% white
        color_dark = np.array([30, 15, 60])      # Dark purple
        color_light = np.array([80, 50, 120])    # Lighter purple
        
        def make_gradient_frame(t):
            """Create a frame with animated gradient + blur"""
            # Animate: slight hue shift over time
            shift = np.sin(t * 0.5) * 10  # Subtle oscillation
            
            frame = np.zeros((height, width, 3), dtype=np.float32)
            
            # Zone 1: Top 30% - White to Dark transition
            zone1_end = int(height * 0.3)
            for y in range(zone1_end):
                ratio = y / zone1_end
                color = color_white * (1 - ratio) + color_dark * ratio
                color = np.clip(color + shift, 0, 255)
                frame[y, :] = color
            
            # Zone 2: Middle 40% - Dark stays mostly dark
            zone2_end = int(height * 0.7)
            for y in range(zone1_end, zone2_end):
                ratio = (y - zone1_end) / (zone2_end - zone1_end)
                color = color_dark * (1 - ratio * 0.3) + color_light * (ratio * 0.3)
                color = np.clip(color + shift * 0.5, 0, 255)
                frame[y, :] = color
            
            # Zone 3: Bottom 30% - Dark to Lighter
            for y in range(zone2_end, height):
                ratio = (y - zone2_end) / (height - zone2_end)
                color = color_dark * (1 - ratio) + color_light * ratio
                color = np.clip(color + shift, 0, 255)
                frame[y, :] = color
            
            # APPLY BLUR EFFECT (sigma=30 for smooth gradient)
            for c in range(3):
                frame[:, :, c] = gaussian_filter(frame[:, :, c], sigma=30)
            
            return frame.astype(np.uint8)
        
        # Create video clip from frames
        clip = VideoClip(make_gradient_frame, duration=duration)
        clip = clip.set_fps(24)
        return clip

    def apply_ken_burns(self, clip, duration, zoom_ratio=1.15):
        """
        Applies a Premium Ken Burns effect (Zoom + Pan) with non-linear easing.
        Mimics GSAP 'Power2.inOut' or Sine ease for professional feel.
        """
        import numpy as np
        
        # Define easing function (Sine InOut)
        def ease_in_out(t):
            return -(np.cos(np.pi * t) - 1) / 2
            
        w, h = clip.w, clip.h
        
        # Directions: 0=Center, 1=TopLeft, 2=BottomRight, 3=TopRight, 4=BottomLeft
        direction = random.choice([0, 1, 2, 3, 4])
        
        def filter(get_frame, t):
            # Normalized time (0 to 1)
            progress = t / duration
            eased_progress = ease_in_out(progress)
            
            # Zoom Factor calculation (1.0 -> 1.15)
            current_zoom = 1.0 + (zoom_ratio - 1.0) * eased_progress
            
            # Calculate dynamic crop window
            # We want to crop a window of size (w/zoom, h/zoom) from the original
            cw, ch = w / current_zoom, h / current_zoom
            
            if direction == 0: # Center Zoom
                x1 = (w - cw) / 2
                y1 = (h - ch) / 2
            elif direction == 1: # Top Left
                x1 = (w - cw) * eased_progress  # Pan slightly
                y1 = (h - ch) * eased_progress
            elif direction == 2: # Bottom Right
                x1 = (w - cw) * (1 - eased_progress)
                y1 = (h - ch) * (1 - eased_progress)
            else: # Random slight pan
                x1 = (w - cw) / 2
                y1 = (h - ch) / 2
                
            frame = get_frame(t)
            
            # Crop and Resize using PIL (cleaner upscaling than basic array slicing)
            from PIL import Image
            img = Image.fromarray(frame)
            cropped = img.crop((x1, y1, x1+cw, y1+ch))
            resized = cropped.resize((1080, 1920), Image.LANCZOS)
            return np.array(resized)

        return clip.fl(filter)

if __name__ == "__main__":
    # Mock Test
    pass
