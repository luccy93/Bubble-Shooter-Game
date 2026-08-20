// storage.js - Enhanced Local Storage Management
// Supports: level progress, star ratings, achievements, statistics, settings, tutorial

const STORAGE_KEYS = {
    PROGRESS: 'bubble_shooter_progress',
    SETTINGS: 'bubble_shooter_settings',
    STATS: 'bubble_shooter_stats',
    ACHIEVEMENTS: 'bubble_shooter_achievements'
};

const StorageManager = {
    // -------------------------------------------------------
    // PROGRESS (levels, scores, stars)
    // -------------------------------------------------------
    getSaveData() {
        return this._safeRead(STORAGE_KEYS.PROGRESS, {
            unlockedLevel: 1,
            highScore: 0,
            levelScores: {},
            levelStars: {},
            tutorialComplete: false
        });
    },

    saveProgress(level, score, stars) {
        const data = this.getSaveData();
        data.levelScores[level] = Math.max(data.levelScores[level] || 0, score);
        data.levelStars[level] = Math.max(data.levelStars[level] || 0, stars || 0);
        if (level >= data.unlockedLevel) {
            data.unlockedLevel = level + 1;
        }
        data.highScore = Math.max(data.highScore, score);
        this._safeWrite(STORAGE_KEYS.PROGRESS, data);
    },

    setTutorialComplete() {
        const data = this.getSaveData();
        data.tutorialComplete = true;
        this._safeWrite(STORAGE_KEYS.PROGRESS, data);
    },

    getTotalStars() {
        const data = this.getSaveData();
        let total = 0;
        for (const key in data.levelStars) {
            total += data.levelStars[key] || 0;
        }
        return total;
    },

    // -------------------------------------------------------
    // SETTINGS
    // -------------------------------------------------------
    getSettings() {
        return this._safeRead(STORAGE_KEYS.SETTINGS, {
            musicEnabled: true,
            sfxEnabled: true,
            hapticsEnabled: true
        });
    },

    saveSettings(settings) {
        this._safeWrite(STORAGE_KEYS.SETTINGS, settings);
    },

    // -------------------------------------------------------
    // STATISTICS
    // -------------------------------------------------------
    getStats() {
        return this._safeRead(STORAGE_KEYS.STATS, {
            levelsCompleted: 0,
            bubblesPopped: 0,
            bubblesDropped: 0,
            highestScore: 0,
            highestCombo: 0,
            perfectClears: 0,
            totalGames: 0,
            totalPlayTimeMs: 0,
            totalShots: 0
        });
    },

    updateStats(updates) {
        const stats = this.getStats();
        for (const key in updates) {
            if (key === 'highestScore' || key === 'highestCombo') {
                stats[key] = Math.max(stats[key] || 0, updates[key]);
            } else if (typeof updates[key] === 'number') {
                stats[key] = (stats[key] || 0) + updates[key];
            }
        }
        this._safeWrite(STORAGE_KEYS.STATS, stats);
    },

    // -------------------------------------------------------
    // ACHIEVEMENTS
    // -------------------------------------------------------
    getAchievements() {
        return this._safeRead(STORAGE_KEYS.ACHIEVEMENTS, {});
    },

    unlockAchievement(id) {
        const achievements = this.getAchievements();
        if (!achievements[id]) {
            achievements[id] = { unlockedAt: Date.now() };
            this._safeWrite(STORAGE_KEYS.ACHIEVEMENTS, achievements);
            return true; // newly unlocked
        }
        return false; // already unlocked
    },

    isAchievementUnlocked(id) {
        const achievements = this.getAchievements();
        return !!achievements[id];
    },

    // -------------------------------------------------------
    // RESET
    // -------------------------------------------------------
    resetAllProgress() {
        try {
            localStorage.removeItem(STORAGE_KEYS.PROGRESS);
            localStorage.removeItem(STORAGE_KEYS.STATS);
            localStorage.removeItem(STORAGE_KEYS.ACHIEVEMENTS);
        } catch (e) {
            console.error('Failed to reset progress', e);
        }
    },

    // -------------------------------------------------------
    // SAFE READ/WRITE HELPERS
    // -------------------------------------------------------
    _safeRead(key, defaults) {
        try {
            const raw = localStorage.getItem(key);
            if (raw) {
                const parsed = JSON.parse(raw);
                // Merge with defaults for forward-compatibility
                return { ...defaults, ...parsed };
            }
        } catch (e) {
            console.error(`Error reading ${key}`, e);
        }
        return { ...defaults };
    },

    _safeWrite(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (e) {
            console.error(`Error writing ${key}`, e);
        }
    }
};
