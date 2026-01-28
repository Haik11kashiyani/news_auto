from moviepy.editor import *
from moviepy.video.fx.all import resize, crop
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
            # 1. Load Audio
            print(f"Loading Audio from: {audio_path}")
            if not os.path.exists(audio_path):
                print("Error: Audio file not found!")
                return None
            
            # Check size
            if os.path.getsize(audio_path) < 100:
                print("Error: Audio file is empty or too small!")
                return None

            audio = AudioFileClip(audio_path)
            duration = audio.duration
            print(f"Audio Duration: {duration}s")
            
            # 2. Prepare Background
            if bg_type == "video":
                bg_clip = VideoFileClip(bg_path, audio=False)
                # Loop if too short
                if bg_clip.duration < duration:
                    bg_clip = bg_clip.loop(duration=duration)
                else:
                    bg_clip = bg_clip.subclip(0, duration)
            else:
                # Image -> Ken Burns Effect
                img = ImageClip(bg_path).set_duration(duration)
                # Simple zoom effect: 1.0 -> 1.1
                bg_clip = img.resize(lambda t: 1 + 0.02 * t) 
            
            # Crop to 9:16 (Vertical) - Center Crop
            # Assuming 1080x1920 target
            w, h = bg_clip.size
            target_ratio = 9/16
            current_ratio = w/h
            
            if current_ratio > target_ratio:
                # Too wide, crop width
                new_w = h * target_ratio
                bg_clip = bg_clip.crop(x1=w/2 - new_w/2, width=new_w, height=h)
            else:
                # Too tall (rare), crop height
                new_h = w / target_ratio
                bg_clip = bg_clip.crop(y1=h/2 - new_h/2, width=w, height=new_h)
                
            bg_clip = bg_clip.resize(newsize=(1080, 1920))

            # 3. Prepare Overlay
            # overlay_path is a directory of frames
            if os.path.isdir(overlay_path):
                # Image Sequence
                overlay_clip = ImageSequenceClip(overlay_path, fps=10) # Matches generator settings
                # Loop overlay to match video duration
                if overlay_clip.duration < duration:
                    overlay_clip = overlay_clip.loop(duration=duration)
                else:
                    overlay_clip = overlay_clip.subclip(0, duration)
            else:
                # Fallback if single image
                overlay_clip = ImageClip(overlay_path).set_duration(duration)

            # 4. Composite
            final_video = CompositeVideoClip([bg_clip, overlay_clip.set_position("center")])
            final_video = final_video.set_audio(audio)
            
            # 5. Write Output
            output_path = os.path.join(self.output_dir, output_filename)
            final_video.write_videofile(
                output_path, 
                fps=24, 
                codec='libx264', 
                audio_codec='aac', 
                threads=4,
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
