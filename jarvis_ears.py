import io
import wave
import numpy as np
import sounddevice as sd
import speech_recognition as sr


class JarvisEars:
    """Professional VAD-powered continuous speech listener with zero fixed-duration lag."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()
        print("[EAR] Pro VAD Speech Engine online (Auto-detects speech start/stop).")

    def listen_command(self) -> str:
        """Listens dynamically: records only when you speak, stops automatically when you pause."""
        print("\n[EAR] Listening... (Speak anytime, auto-stops when you finish)")
        
        chunk_duration = 0.1  # 100ms audio chunks
        chunk_samples = int(self.sample_rate * chunk_duration)
        threshold = 450       # RMS energy threshold for speech sensitivity
        silence_limit = 0.6   # Seconds of silence to determine you've finished speaking
        
        frames = []
        speaking = False
        silent_chunks = 0
        max_silent_chunks = int(silence_limit / chunk_duration)

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16') as stream:
                while True:
                    audio_chunk, overflowed = stream.read(chunk_samples)
                    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
                    
                    # Calculate real-time volume energy (RMS)
                    rms = np.sqrt(np.mean(audio_data.astype(float)**2))

                    if rms > threshold:
                        if not speaking:
                            print("[EAR] Speech detected, recording...")
                            speaking = True
                        frames.append(audio_chunk)
                        silent_chunks = 0  # Reset silence counter while speaking
                    elif speaking:
                        frames.append(audio_chunk)
                        silent_chunks += 1
                        if silent_chunks > max_silent_chunks:
                            # User stopped talking; exit capture loop
                            break

            if not frames:
                return ""

            # Combine collected audio chunks into a single numpy buffer
            audio_np = np.concatenate([np.frombuffer(f, dtype=np.int16) for f in frames])

            # Pack into an in-memory WAV buffer
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_np.tobytes())
            wav_io.seek(0)

            # Send clean audio snippet for recognition
            with sr.AudioFile(wav_io) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data).lower().strip()
                print(f"[EAR] Recognized: '{text}'")
                return text

        except sr.UnknownValueError:
            print("[EAR] Didn't quite catch that. Try speaking clearly.")
            return ""
        except sr.RequestError as e:
            print(f"[!] Network service error: {e}")
            return ""
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            print(f"[!] Audio stream error: {e}")
            return ""