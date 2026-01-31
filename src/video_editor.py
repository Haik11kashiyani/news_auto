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
            
            # 1. Output Path
            output_path = os.path.join(self.output_dir, output_filename)
            print(f"Assembling video: {output_path}")

            # 2. Build Sequence from Segments (Define Duration First)
            # segments = [{"audio": path, "image": path}, ...]
            if isinstance(overlay_path, list) and len(overlay_path) > 0 and isinstance(overlay_path[0], dict):
                # New Segment Logic
                clips = []
                audio_clips = []
                
                print(f"Assembling {len(overlay_path)} synced segments...")
                
                for seg in overlay_path:
                    a_path = seg.get("audio")
                    i_path = seg.get("image")
                    
                    if not a_path or not i_path:
                        continue
                        
                    # Load Audio
                    ac = AudioFileClip(a_path)
                    seg_duration = ac.duration
                    audio_clips.append(ac)
                    
                    # Load Image & Set Duration
                    ic = ImageClip(i_path).set_duration(seg_duration).resize(newsize=(1080, 1920))
                    clips.append(ic)
                
                if not clips:
                    print("No valid segments found.")
                    return None
                    
                # Concatenate
                overlay_clip = concatenate_videoclips(clips)
                final_audio = concatenate_audioclips(audio_clips)
                duration = final_audio.duration
                
            else:
                # Fallback / Single Image Logic
                if isinstance(overlay_path, list):
                     # Legacy fallback
                     img_path = overlay_path[0]
                else:
                     img_path = overlay_path

                # Load Audio First to get duration
                final_audio = AudioFileClip(audio_path)
                duration = final_audio.duration
                
                overlay_clip = ImageClip(img_path, duration=duration)
                overlay_clip = overlay_clip.resize(newsize=(1080, 1920))
            
            # Position Center
            overlay_clip = overlay_clip.set_position("center")

            # 1. Background Layer (Full Duration)
            if not bg_path or not os.path.exists(bg_path):
                print("Warning: Background not found. Using Black Fallback.")
                bg_clip = ColorClip(size=(1080, 1920), color=(0,0,0), duration=duration)
            elif bg_type == "video":
                # Loop video if shorter than audio
                bg_clip = VideoFileClip(bg_path, audio=False)
                if bg_clip.duration < duration:
                    bg_clip = vfx.loop(bg_clip, duration=duration)
                else:
                    bg_clip = bg_clip.subclip(0, duration)
                bg_clip = bg_clip.resize(height=1920).crop(x1=0, y1=0, width=1080, height=1920)
            else:
                # Image with Pan/Zoom
                img = ImageClip(bg_path).set_duration(duration)
                # Subtle zoom effect
                bg_clip = img.resize(lambda t: 1 + 0.02 * t)

            # 4. Composite
            print("Compositing Layers...")
            # We explicitly tell MoviePy to use the alpha of the overlay
            # Using 'compose' method or just list
            final_video = CompositeVideoClip([bg_clip, overlay_clip], size=(1080,1920))
            final_video = final_video.set_duration(duration)
            final_video = CompositeVideoClip([bg_clip, overlay_clip], size=(1080,1920))
            final_video = final_video.set_duration(duration)
            final_video = final_video.set_audio(final_audio)
            
            # 5. Write Output
            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, output_filename)
            final_video.write_videofile(
                output_path, 
                fps=24, 
                codec='libx264', 
                audio_codec='aac', 
                threads=1, # Single thread for safety with Alpha compositing
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True
            )
            
            return output_path

        except Exception as e:
            print(f"Error editing video: {e}")
            return None

if __name__ == "__main__":
    # Mock Test
    pass
