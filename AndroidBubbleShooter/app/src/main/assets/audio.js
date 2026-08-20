// audio.js - Enhanced Audio Manager with synthesized SFX via Web Audio API
// No additional audio files needed - generates SFX procedurally

const AudioManager = {
    scene: null,
    bgMusic: null,
    audioCtx: null,

    init(scene) {
        this.scene = scene;
        // Create Web Audio context for synthesized SFX
        try {
            this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('Web Audio API not available for SFX synthesis', e);
        }
    },

    playMusic(key, loop = true) {
        const settings = StorageManager.getSettings();
        if (!settings.musicEnabled) return;

        if (this.bgMusic && this.bgMusic.isPlaying) {
            // Don't restart if same track already playing
            if (this.bgMusic.key === key) return;
            this.bgMusic.stop();
        }

        try {
            this.bgMusic = this.scene.sound.add(key, { loop: loop, volume: 0.35 });
            this.bgMusic.play();
        } catch (e) {
            console.warn('Failed to play background music', e);
        }
    },

    stopMusic() {
        if (this.bgMusic) {
            try { this.bgMusic.stop(); } catch (e) {}
        }
    },

    playSFX(key) {
        const settings = StorageManager.getSettings();
        if (!settings.sfxEnabled) return;

        // Use Phaser sound if available
        try {
            if (this.scene && this.scene.cache.audio.exists(key)) {
                this.scene.sound.play(key, { volume: 0.7 });
                return;
            }
        } catch (e) {}

        // Fallback to synthesized SFX
        this._playSynthSFX(key);
    },

    // Synthesized SFX using Web Audio API
    _playSynthSFX(type) {
        if (!this.audioCtx) return;
        const settings = StorageManager.getSettings();
        if (!settings.sfxEnabled) return;

        try {
            const ctx = this.audioCtx;
            if (ctx.state === 'suspended') ctx.resume();

            switch (type) {
                case 'pop':
                    this._synthPop(ctx);
                    break;
                case 'shoot':
                    this._synthShoot(ctx);
                    break;
                case 'combo':
                    this._synthCombo(ctx);
                    break;
                case 'victory':
                    this._synthVictory(ctx);
                    break;
                case 'failure':
                    this._synthFailure(ctx);
                    break;
                case 'button':
                    this._synthButton(ctx);
                    break;
                case 'unlock':
                    this._synthUnlock(ctx);
                    break;
                case 'drop':
                    this._synthDrop(ctx);
                    break;
                case 'star':
                    this._synthStar(ctx);
                    break;
                default:
                    this._synthButton(ctx);
            }
        } catch (e) {
            // Silently fail - audio is non-critical
        }
    },

    _synthPop(ctx) {
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(200, now + 0.1);
        gain.gain.setValueAtTime(0.3, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
        osc.connect(gain).connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.12);
    },

    _synthShoot(ctx) {
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(300, now);
        osc.frequency.exponentialRampToValueAtTime(600, now + 0.08);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
        osc.connect(gain).connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.1);
    },

    _synthCombo(ctx) {
        const now = ctx.currentTime;
        [523, 659, 784].forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.25, now + i * 0.08);
            gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.08 + 0.15);
            osc.connect(gain).connect(ctx.destination);
            osc.start(now + i * 0.08);
            osc.stop(now + i * 0.08 + 0.15);
        });
    },

    _synthVictory(ctx) {
        const now = ctx.currentTime;
        [523, 659, 784, 1047].forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.2, now + i * 0.12);
            gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.12 + 0.25);
            osc.connect(gain).connect(ctx.destination);
            osc.start(now + i * 0.12);
            osc.stop(now + i * 0.12 + 0.25);
        });
    },

    _synthFailure(ctx) {
        const now = ctx.currentTime;
        [400, 350, 280].forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.2, now + i * 0.15);
            gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.15 + 0.2);
            osc.connect(gain).connect(ctx.destination);
            osc.start(now + i * 0.15);
            osc.stop(now + i * 0.15 + 0.2);
        });
    },

    _synthButton(ctx) {
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.value = 600;
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.06);
        osc.connect(gain).connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.06);
    },

    _synthUnlock(ctx) {
        const now = ctx.currentTime;
        [440, 554, 659, 880].forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.18, now + i * 0.1);
            gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.1 + 0.2);
            osc.connect(gain).connect(ctx.destination);
            osc.start(now + i * 0.1);
            osc.stop(now + i * 0.1 + 0.2);
        });
    },

    _synthDrop(ctx) {
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(500, now);
        osc.frequency.exponentialRampToValueAtTime(100, now + 0.25);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
        osc.connect(gain).connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.25);
    },

    _synthStar(ctx) {
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(1760, now + 0.15);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        osc.connect(gain).connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.2);
    },

    updateSettings() {
        const settings = StorageManager.getSettings();
        if (this.bgMusic) {
            if (settings.musicEnabled && !this.bgMusic.isPlaying) {
                try { this.bgMusic.play(); } catch (e) {}
            } else if (!settings.musicEnabled && this.bgMusic.isPlaying) {
                try { this.bgMusic.stop(); } catch (e) {}
            }
        }
    }
};
