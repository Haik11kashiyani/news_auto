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
            
            # Load Audio First to get duration
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            print(f"Audio Duration: {duration}s")

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
            # Use strict ImageClip for the static PNG sequence
            try:
                if isinstance(overlay_path, list):
                    # Multi-Slide logic: Split total duration equally
                    num_slides = len(overlay_path)
                    slide_duration = duration / num_slides
                    clips = []
                    for path in overlay_path:
                        clip = ImageClip(path).set_duration(slide_duration).resize(newsize=(1080, 1920))
                        clips.append(clip)
                    overlay_clip = concatenate_videoclips(clips)
                else:
                    # Single Slide logic
                    overlay_clip = ImageClip(overlay_path, duration=duration)
                    # Resize to fit just in case, though it should match viewport
                    overlay_clip = overlay_clip.resize(newsize=(1080, 1920))
            except Exception as e:
                print(f"Failed to load overlay image(s): {e}")
                return None

            # Position Center
            overlay_clip = overlay_clip.set_position("center")

            # 4. Composite
            print("Compositing Layers...")
            # We explicitly tell MoviePy to use the alpha of the overlay
            # Using 'compose' method or just list
            final_video = CompositeVideoClip([bg_clip, overlay_clip], size=(1080,1920))
            final_video = final_video.set_duration(duration)
            final_video = final_video.set_audio(audio)
            
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
