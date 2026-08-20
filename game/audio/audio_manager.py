# game/audio/audio_manager.py - Central audio management and fallback synthesizers

import pygame
import os
import math
import struct
from game.core.config import GameConfig
from game.storage.save_manager import SaveManager

class AudioManager:
    _initialized = False
    _music_playing = None
    _sfx_cache = {}

    @classmethod
    def init(cls):
        """Initializes the mixer and pre-loads/synthesizes sound effects."""
        if cls._initialized:
            return

        try:
            pygame.mixer.init()
            cls._initialized = True
        except Exception as e:
            # Safe degradation if audio device is unavailable
            cls._initialized = False
            return

        # Pre-load or synthesize core sounds
        cls._load_or_synthesize('pop', 'popcork.ogg', cls._synth_pop)
        cls._load_or_synthesize('shoot', 'shoot.ogg', cls._synth_shoot)
        cls._load_or_synthesize('combo', 'combo.ogg', cls._synth_combo)
        cls._load_or_synthesize('victory', 'victory.ogg', cls._synth_victory)
        cls._load_or_synthesize('failure', 'failure.ogg', cls._synth_failure)
        cls._load_or_synthesize('button', 'button.ogg', cls._synth_button)
        cls._load_or_synthesize('star', 'star.ogg', cls._synth_star)

    @classmethod
    def _load_or_synthesize(cls, key, filename, synth_func):
        """Loads SFX from assets or synthesizes it procedurally as fallback."""
        if not cls._initialized:
            return

        path = GameConfig.get_asset_path('audio', filename)
        if os.path.exists(path):
            try:
                cls._sfx_cache[key] = pygame.mixer.Sound(path)
                return
            except Exception:
                pass

        # Synthesize fallback in-memory buffer
        try:
            cls._sfx_cache[key] = synth_func()
        except Exception:
            pass

    @classmethod
    def play_music(cls, filename, loop=-1):
        """Plays background music if enabled."""
        if not cls._initialized:
            return

        settings = SaveManager.get_settings()
        if not settings["music"]:
            return

        # Don't restart if already playing this track
        if cls._music_playing == filename:
            return

        path = GameConfig.get_asset_path('audio', filename)
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(loop)
                cls._music_playing = filename
            except Exception:
                cls._music_playing = None

    @classmethod
    def stop_music(cls):
        if cls._initialized:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            cls._music_playing = None

    @classmethod
    def update_settings(cls):
        """Updates music playback according to active settings."""
        if not cls._initialized:
            return

        settings = SaveManager.get_settings()
        if not settings["music"]:
            cls.stop_music()

    @classmethod
    def play_sfx(cls, key):
        """Plays SFX if enabled."""
        if not cls._initialized:
            return

        settings = SaveManager.get_settings()
        if not settings["sfx"]:
            return

        sound = cls._sfx_cache.get(key)
        if sound:
            try:
                sound.set_volume(0.6)
                sound.play()
            except Exception:
                pass

    # -------------------------------------------------------
    # PROCEDURAL SFX SYNTHESIZERS (Generates 16-bit Mono Mono Sound buffers)
    # -------------------------------------------------------
    @classmethod
    def _create_sound_from_samples(cls, samples, sample_rate=22050):
        """Converts sample array into a pygame.mixer.Sound object."""
        packed = b"".join(struct.pack("<h", int(s)) for s in samples)
        # Write WAV format headers
        channels = 1
        bytes_per_sample = 2
        byte_rate = sample_rate * channels * bytes_per_sample
        block_align = channels * bytes_per_sample
        data_len = len(packed)
        
        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", 36 + data_len, b"WAVE",
            b"fmt ", 16, 1, channels, sample_rate, byte_rate, block_align, 16,
            b"data", data_len
        )
        return pygame.mixer.Sound(buffer=wav_header + packed)

    @classmethod
    def _synth_pop(cls):
        # Quick descending frequency pitch
        samples = []
        duration = 0.08
        rate = 22050
        for i in range(int(rate * duration)):
            t = i / rate
            freq = 600 - t * 4500  # Descending
            freq = max(100, freq)
            val = math.sin(2 * math.pi * freq * t) * 32767 * (1 - t / duration)
            samples.append(val)
        return cls._create_sound_from_samples(samples, rate)

    @classmethod
    def _synth_shoot(cls):
        # Sweeping ascending frequency pitch
        samples = []
        duration = 0.1
        rate = 22050
        for i in range(int(rate * duration)):
            t = i / rate
            freq = 200 + t * 3000  # Ascending
            val = math.sin(2 * math.pi * freq * t) * 25000 * (1 - t / duration)
            samples.append(val)
        return cls._create_sound_from_samples(samples, rate)

    @classmethod
    def _synth_combo(cls):
        # Quick dual chord
        samples = []
        duration = 0.25
        rate = 22050
        for i in range(int(rate * duration)):
            t = i / rate
            val1 = math.sin(2 * math.pi * 523 * t)  # C5
            val2 = math.sin(2 * math.pi * 659 * t)  # E5
            val = (val1 + val2) * 0.5 * 25000 * (1 - t / duration)
            samples.append(val)
        return cls._create_sound_from_samples(samples, rate)

    @classmethod
    def _synth_victory(cls):
        # Rising arpeggio
        samples = []
        duration = 0.5
        rate = 22050
        notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
        note_dur = duration / len(notes)
        for i in range(int(rate * duration)):
            t = i / rate
            note_idx = int(t / note_dur)
            freq = notes[min(note_idx, len(notes)-1)]
            val = math.sin(2 * math.pi * freq * t) * 20000 * (1 - t / duration)
            samples.append(val)
        return cls._create_sound_from_samples(samples, rate)

    @classmethod
    def _synth_failure(cls):
        # Stuttering descending pitch
        samples = []
        duration = 0.5
        rate = 22050
        for i in range(int(rate * duration)):
            t = i / rate
            freq = 300 - int(t * 4) * 40 - (t * 100)
            freq = max(60, freq)
            val = math.sin(2 * math.pi * freq * t) * 20000 * (1 - t / duration)
            samples.append(val)
        return cls._create_sound_from_samples(samples, rate)

    @classmethod
    def _synth_button(cls):
        # Soft click
        samples = []
        duration = 0.05
        rate = 22050
        for i in range(int(rate * duration)):
            t = i / rate
            val = math.sin(2 * math.pi * 800 * t) * 15000 * (1 - t / duration)
            samples.append(val)
        return cls._create_sound_from_samples(samples, rate)

    @classmethod
    def _synth_star(cls):
        # High bell chime
        samples = []
        duration = 0.25
        rate = 22050
        for i in range(int(rate * duration)):
            t = i / rate
            val = math.sin(2 * math.pi * 1200 * t) * 20000 * math.exp(-12 * t)
            samples.append(val)
        return cls._create_sound_from_samples(samples, rate)
