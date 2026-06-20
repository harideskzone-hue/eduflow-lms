document.addEventListener('DOMContentLoaded', () => {
    if (!window.eduflowEvents || window.eduflowEvents.length === 0) return;
    
    let isPlaying = false;
    
    function processNext() {
        if (isPlaying || window.eduflowEvents.length === 0) return;
        isPlaying = true;
        const event = window.eduflowEvents.shift();
        
        playEvent(event).then(() => {
            isPlaying = false;
            processNext();
        });
    }
    
    function playEvent(evt) {
        return new Promise((resolve) => {
            if (evt.type === 'xp_toast') {
                showXPToast(evt).then(resolve);
            } else if (evt.type === 'achievement') {
                showAchievementModal(evt).then(resolve);
            } else if (evt.type === 'milestone') {
                showMilestoneModal(evt).then(resolve);
            } else if (evt.type === 'confetti') {
                showConfetti().then(resolve);
            } else {
                resolve();
            }
        });
    }
    
    // P7.2 XP Toasts
    function showXPToast(evt) {
        return new Promise(resolve => {
            const toast = document.createElement('div');
            toast.className = 'xp-toast';
            toast.innerHTML = `
                <div class="xp-toast-icon"><i data-lucide="zap"></i></div>
                <div class="xp-toast-content">
                    <div class="xp-toast-title">+${evt.xp} XP</div>
                    <div class="xp-toast-desc">${evt.message}</div>
                </div>
            `;
            document.body.appendChild(toast);
            if (window.lucide) window.lucide.createIcons();
            
            // Force reflow
            void toast.offsetWidth;
            
            toast.classList.add('show');
            
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => {
                    toast.remove();
                    resolve();
                }, 300);
            }, 2500); // 2.5s display
        });
    }

    // P7.3 Achievement Modal
    function showAchievementModal(evt) {
        return new Promise(resolve => {
            const overlay = document.createElement('div');
            overlay.className = 'celebration-overlay';
            overlay.innerHTML = `
                <div class="achievement-modal">
                    <div class="achievement-modal-badge">
                        <i data-lucide="${evt.icon || 'award'}"></i>
                    </div>
                    <div class="achievement-modal-title">Achievement Unlocked</div>
                    <div class="achievement-modal-name">${evt.title}</div>
                    <button class="btn btn-primary" id="btn-continue-ach">Continue</button>
                </div>
            `;
            document.body.appendChild(overlay);
            if (window.lucide) window.lucide.createIcons();
            
            // Force reflow
            void overlay.offsetWidth;
            overlay.classList.add('show');
            
            document.getElementById('btn-continue-ach').addEventListener('click', () => {
                overlay.classList.remove('show');
                setTimeout(() => {
                    overlay.remove();
                    resolve();
                }, 300);
            });
        });
    }

    // P7.4 Milestone Celebrations
    function showMilestoneModal(evt) {
        return new Promise(resolve => {
            const overlay = document.createElement('div');
            overlay.className = 'celebration-overlay';
            overlay.innerHTML = `
                <div class="milestone-modal">
                    <div class="milestone-modal-icon">
                        <i data-lucide="target"></i>
                    </div>
                    <div class="milestone-modal-title">Milestone Reached</div>
                    <div class="milestone-modal-path">${evt.path_name}</div>
                    <div class="milestone-modal-progress">${evt.progress}% Complete</div>
                    <button class="btn btn-secondary" style="border-color: var(--accent-gold); color: var(--accent-gold);" id="btn-continue-mile">Keep Going</button>
                </div>
            `;
            document.body.appendChild(overlay);
            if (window.lucide) window.lucide.createIcons();
            
            // Force reflow
            void overlay.offsetWidth;
            overlay.classList.add('show');
            
            document.getElementById('btn-continue-mile').addEventListener('click', () => {
                overlay.classList.remove('show');
                setTimeout(() => {
                    overlay.remove();
                    resolve();
                }, 300);
            });
        });
    }

    // P7.5 Confetti
    function showConfetti() {
        return new Promise(resolve => {
            const duration = 3000;
            const end = Date.now() + duration;

            (function frame() {
                confetti({
                    particleCount: 5,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 },
                    colors: ['#2563EB', '#D4AF37', '#1E293B']
                });
                confetti({
                    particleCount: 5,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1 },
                    colors: ['#2563EB', '#D4AF37', '#1E293B']
                });

                if (Date.now() < end) {
                    requestAnimationFrame(frame);
                } else {
                    resolve();
                }
            }());
        });
    }

    // Start queue
    processNext();
});
