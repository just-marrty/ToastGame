class Game {
    constructor() {
        this.svg = document.getElementById('game');
        this.toastSymbolId = '#toast';
        this.scoreEl = document.getElementById('score');
        this.livesEl = document.getElementById('lives');
        this.finalScoreInfoEl = document.getElementById('final-score-info');
        this.gameOverScreenEl = document.getElementById('game-over-screen');
        this.pauseBtn = document.getElementById('pauseBtn');
        this.playBtn = document.getElementById('playBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.toasts = [];
        this.score = 0;
        this.spawnInterval = 1500;
        this.remainingLives = 5;
        this.gameOver = false;
        this.isPaused = false;
        this.difficultyLevel = 1;
        this.toastsPerSpawn = 1;
        this.baseDuration = 2500;

        this.elapsedTime = 0;
        this.lastTimestamp = null;
        this.pauseTime = 0;
        this.lastDifficultyIncrease = 0;
        this.rafId = null;

        this.loop = this.loop.bind(this);

        this.pauseBtn.addEventListener('click', () => this.pauseGame());
        this.playBtn.addEventListener('click', () => this.resumeGame());
        this.stopBtn.addEventListener('click', () => this.stopGame());

        this.startSpawnTimer();
        this.updateLives();
        this.rafId = requestAnimationFrame(this.loop);
    }

    getToastDuration() {
        return Math.max(1000, this.baseDuration - (this.difficultyLevel - 1) * 200);
    }

    updateDifficulty() {
        const timeSinceLastIncrease = (this.elapsedTime - this.lastDifficultyIncrease) / 1000;
        if (timeSinceLastIncrease >= 20) {
            this.difficultyLevel++;
            this.lastDifficultyIncrease = this.elapsedTime;
            this.toastsPerSpawn = Math.min(5, 1 + Math.floor(this.difficultyLevel / 2));
            this.spawnInterval = Math.max(200, 1500 - (this.difficultyLevel - 1) * 150);
            this.toasts.forEach(toast => {
                toast.duration = this.getToastDuration();
            });
            this.startSpawnTimer();
        }
    }

    pauseGame() {
        if (!this.gameOver) {
            this.isPaused = true;
            this.pauseTime = performance.now();
            this.pauseBtn.disabled = true;
            this.playBtn.disabled = false;
            clearInterval(this.spawnTimer);
        }
    }

    resumeGame() {
        if (!this.gameOver && this.isPaused) {
            const now = performance.now();
            const pauseDuration = now - this.pauseTime;
            this.lastTimestamp += pauseDuration; // posuň čas, aby delta nebyla velká

            this.pauseBtn.disabled = false;
            this.playBtn.disabled = true;
            this.isPaused = false;
            this.startSpawnTimer();
        }
    }

    stopGame() {
        this.gameOver = true;
        clearInterval(this.spawnTimer);
        this.gameOverScreenEl.setAttribute('visibility', 'visible');
        this.finalScoreInfoEl.textContent = `Final Score: ${this.score}`;
        this.pauseBtn.disabled = true;
        this.playBtn.disabled = true;
        this.stopBtn.disabled = true;
        this.saveScore();
    }

    startSpawnTimer() {
        if (this.spawnTimer) clearInterval(this.spawnTimer);
        this.spawnTimer = setInterval(() => {
            if (!this.gameOver && !this.isPaused) {
                this.spawnToast();
            }
        }, this.spawnInterval);
    }

    spawnToast() {
        for (let i = 0; i < this.toastsPerSpawn; i++) {
            const startX = Math.random() * 350 + 25;
            const endX = Math.random() * 350 + 25;
            const peakY = 200 + Math.random() * 50;
            const toast = document.createElementNS('http://www.w3.org/2000/svg', 'use');
            toast.setAttribute('href', this.toastSymbolId);
            toast.setAttribute('class', 'toast');
            toast.setAttribute('x', startX);
            toast.setAttribute('y', 680);
            this.svg.appendChild(toast);
            const toastObj = {
                el: toast,
                startX,
                endX,
                startY: 680,
                peakY,
                startTime: this.elapsedTime, // ⬅ relativní čas!
                duration: this.getToastDuration(),
                clicked: false,
                upwardSpeed: -8,
                reachedBottom: false
            };
            toast.addEventListener('pointerdown', () => {
                if (!this.gameOver && !toastObj.clicked) {
                    this.score += 1;
                    this.scoreEl.textContent = this.score.toString().padStart(8, '0');
                    toastObj.clicked = true;
                }
            });
            this.toasts.push(toastObj);
        }
    }

    loop(timestamp) {
        this.rafId = requestAnimationFrame(this.loop);

        if (this.gameOver || this.isPaused) return;

        if (this.lastTimestamp === null) {
            this.lastTimestamp = timestamp;
        }

        const delta = timestamp - this.lastTimestamp;
        this.lastTimestamp = timestamp;
        this.elapsedTime += delta;

        this.updateDifficulty();

        this.toasts = this.toasts.filter(toast => {
            if (toast.clicked) {
                const currentY = parseFloat(toast.el.getAttribute('y'));
                const newY = currentY + toast.upwardSpeed;
                toast.el.setAttribute('y', newY);
                toast.el.setAttribute('pointer-events', 'none');
                if (newY < -50) {
                    toast.el.remove();
                    return false;
                }
            } else {
                const t = (this.elapsedTime - toast.startTime) / toast.duration;
                if (t > 1) {
                    if (!toast.reachedBottom) {
                        this.remainingLives--;
                        this.updateLives();
                        this.checkGameOver();
                        toast.reachedBottom = true;
                    }
                    toast.el.remove();
                    return false;
                }
                const x = toast.startX + (toast.endX - toast.startX) * t;
                const y = toast.startY - (4 * t * (1 - t)) * (toast.startY - toast.peakY);
                toast.el.setAttribute('x', x);
                toast.el.setAttribute('y', y);
            }
            return true;
        });
    }

    updateLives() {
        this.livesEl.textContent = `${this.remainingLives}X`;
    }

    checkGameOver() {
        if (this.remainingLives <= 0) {
            this.stopGame();
        }
    }

    saveScore() {
        fetch('/save-score/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: new URLSearchParams({ score: this.score })
        }).catch(err => {
            console.error('Nepodařilo se uložit skóre:', err);
        });
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            for (let cookie of document.cookie.split(';')) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Game();
});

