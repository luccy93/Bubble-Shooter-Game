// levels.js - Level definitions with world metadata and star thresholds

const LevelManager = {
    worlds: [
        {
            name: 'Forest Valley',
            icon: '🌿',
            color: 0x34c759,
            bgGradientTop: 0x0b3d0b,
            bgGradientBot: 0x1a4a1a
        },
        {
            name: 'Crystal Cave',
            icon: '💎',
            color: 0x007aff,
            bgGradientTop: 0x0a1628,
            bgGradientBot: 0x0f2847
        },
        {
            name: 'Sunset Desert',
            icon: '🏜️',
            color: 0xff9500,
            bgGradientTop: 0x2d1810,
            bgGradientBot: 0x4a2512
        }
    ],

    levels: [
        // ===== WORLD 1: Forest Valley (Levels 1-5) =====
        // Level 1: Easy intro
        {
            world: 0,
            moves: 24,
            stars: [1000, 2000, 3500],
            grid: [
                [0, 0, 1, 1, 2, 2, 3, 3],
                [0, 1, 1, 2, 2, 3, 3],
                [4, 4, 0, 0, 1, 1, 2, 2],
                [4, 0, 0, 1, 1, 2, 2],
                [-1, -1, -1, -1, -1, -1, -1, -1]
            ]
        },
        // Level 2: Stripes
        {
            world: 0,
            moves: 20,
            stars: [1500, 2500, 4000],
            grid: [
                [1, 1, 2, 2, 1, 1, 2, 2],
                [3, 3, 4, 4, 3, 3, 4],
                [1, 1, 2, 2, 1, 1, 2, 2],
                [3, 3, 4, 4, 3, 3, 4],
                [-1, -1, -1, -1, -1, -1, -1, -1]
            ]
        },
        // Level 3: Checkerboard
        {
            world: 0,
            moves: 18,
            stars: [2000, 3000, 4500],
            grid: [
                [0, 1, 0, 1, 0, 1, 0, 1],
                [2, 3, 2, 3, 2, 3, 2],
                [4, 0, 4, 0, 4, 0, 4, 0],
                [1, 2, 1, 2, 1, 2, 1],
                [3, 4, 3, 4, 3, 4, 3, 4]
            ]
        },
        // Level 4: V-shape
        {
            world: 0,
            moves: 22,
            stars: [2500, 3500, 5000],
            grid: [
                [2, 2, 0, 0, 0, 0, 2, 2],
                [2, 1, 1, 1, 1, 2, 2],
                [3, 3, 1, 4, 4, 1, 3, 3],
                [3, 4, 4, 4, 4, 3],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ]
        },
        // Level 5: Heart
        {
            world: 0,
            moves: 25,
            stars: [2000, 3500, 5000],
            grid: [
                [-1, 0, 0, -1, -1, 0, 0, -1],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [-1, 0, 0, 0, 0, 0, -1],
                [-1, -1, 0, 0, 0, -1, -1, -1],
                [-1, -1, -1, 0, -1, -1, -1]
            ]
        },

        // ===== WORLD 2: Crystal Cave (Levels 6-10) =====
        // Level 6: Diamond
        {
            world: 1,
            moves: 22,
            stars: [2500, 4000, 6000],
            grid: [
                [-1, -1, -1, 1, 1, -1, -1, -1],
                [-1, -1, 2, 2, 2, -1, -1],
                [-1, 3, 3, 0, 0, 3, -1, -1],
                [4, 4, 0, 1, 1, 0, 4],
                [-1, 3, 3, 0, 0, 3, -1, -1],
                [-1, -1, 2, 2, 2, -1, -1]
            ]
        },
        // Level 7: Zigzag
        {
            world: 1,
            moves: 20,
            stars: [3000, 4500, 6500],
            grid: [
                [0, 0, -1, -1, 1, 1, -1, -1],
                [-1, 2, 2, -1, -1, 3, 3],
                [-1, -1, 4, 4, -1, -1, 0, 0],
                [1, 1, -1, -1, 2, 2, -1],
                [3, 3, 3, 3, 3, 3, 3, 3],
                [4, 4, 4, 4, 4, 4, 4]
            ]
        },
        // Level 8: Fortress
        {
            world: 1,
            moves: 18,
            stars: [3500, 5000, 7000],
            grid: [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [1, -1, -1, -1, -1, -1, 1],
                [1, 2, 2, 2, 2, 2, 1, -1],
                [1, -1, 3, 3, 3, -1, 1],
                [1, 4, 4, 4, 4, 4, 1, -1],
                [0, 0, 0, 0, 0, 0, 0]
            ]
        },
        // Level 9: Spiral
        {
            world: 1,
            moves: 22,
            stars: [3000, 5000, 7500],
            grid: [
                [0, 1, 2, 3, 4, 0, 1, 2],
                [2, 3, 4, 0, 1, 2, 3],
                [4, 0, 1, 2, 3, 4, 0, 1],
                [1, 2, 3, 4, 0, 1, 2],
                [-1, -1, -1, -1, -1, -1, -1, -1]
            ]
        },
        // Level 10: Crystal Crown
        {
            world: 1,
            moves: 20,
            stars: [4000, 6000, 8000],
            grid: [
                [1, -1, 2, -1, 3, -1, 4, -1],
                [1, 1, 2, 2, 3, 3, 4],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [1, 1, 2, 2, 3, 3, 4],
                [1, 1, 1, 1, 1, 1, 1, 1],
                [-1, 0, 0, 0, 0, 0, -1]
            ]
        },

        // ===== WORLD 3: Sunset Desert (Levels 11-15) =====
        // Level 11: Pyramid
        {
            world: 2,
            moves: 22,
            stars: [4000, 6000, 8500],
            grid: [
                [-1, -1, -1, 0, 0, -1, -1, -1],
                [-1, -1, 1, 1, 1, -1, -1],
                [-1, 2, 2, 2, 2, 2, -1, -1],
                [3, 3, 3, 3, 3, 3, 3],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [0, 0, 0, 0, 0, 0, 0]
            ]
        },
        // Level 12: Oasis
        {
            world: 2,
            moves: 20,
            stars: [4500, 6500, 9000],
            grid: [
                [2, 2, -1, -1, -1, -1, 2, 2],
                [2, -1, 1, 1, 1, -1, 2],
                [-1, -1, 1, 0, 0, 1, -1, -1],
                [-1, 1, 0, 3, 3, 0, 1],
                [-1, -1, 1, 0, 0, 1, -1, -1],
                [-1, 4, 4, 4, 4, 4, -1]
            ]
        },
        // Level 13: Sandstorm
        {
            world: 2,
            moves: 18,
            stars: [5000, 7000, 9500],
            grid: [
                [0, 1, 2, 3, 4, 0, 1, 2],
                [3, 4, 0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4, 0, 1, 2],
                [3, 4, 0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4, 0, 1, 2],
                [3, 4, 0, 1, 2, 3, 4]
            ]
        },
        // Level 14: Scorpion
        {
            world: 2,
            moves: 20,
            stars: [5000, 7500, 10000],
            grid: [
                [0, 0, 0, -1, -1, 0, 0, 0],
                [1, 1, -1, -1, 1, 1, -1],
                [2, 2, 2, 2, 2, 2, 2, 2],
                [3, -1, 3, -1, 3, -1, 3],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [0, -1, 1, -1, 2, -1, 3]
            ]
        },
        // Level 15: Sun Temple
        {
            world: 2,
            moves: 25,
            stars: [5000, 8000, 12000],
            grid: [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1, 1, 1],
                [2, 2, 2, 2, 2, 2, 2, 2],
                [3, 3, 3, 3, 3, 3, 3],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [0, 0, 0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1, 1, 1, 1]
            ]
        }
    ],

    getLevel(levelNum) {
        const index = Math.max(0, Math.min(levelNum - 1, this.levels.length - 1));
        const level = JSON.parse(JSON.stringify(this.levels[index]));
        return level;
    },

    getWorld(levelNum) {
        const index = Math.max(0, Math.min(levelNum - 1, this.levels.length - 1));
        const worldIdx = this.levels[index].world || 0;
        return this.worlds[worldIdx];
    },

    getWorldForIndex(worldIdx) {
        return this.worlds[Math.max(0, Math.min(worldIdx, this.worlds.length - 1))];
    },

    getLevelsForWorld(worldIdx) {
        const result = [];
        for (let i = 0; i < this.levels.length; i++) {
            if ((this.levels[i].world || 0) === worldIdx) {
                result.push({ levelNum: i + 1, data: this.levels[i] });
            }
        }
        return result;
    },

    getTotalLevels() {
        return this.levels.length;
    },

    calculateStars(levelNum, score) {
        const level = this.getLevel(levelNum);
        const thresholds = level.stars || [1000, 2000, 3000];
        if (score >= thresholds[2]) return 3;
        if (score >= thresholds[1]) return 2;
        if (score >= thresholds[0]) return 1;
        return 0;
    }
};
