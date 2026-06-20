document.addEventListener('DOMContentLoaded', () => {
    const palette = document.getElementById('commandPalette');
    const input = document.getElementById('cmdPaletteInput');
    const list = document.getElementById('cmdPaletteList');
    
    if (!palette) return;

    let isOpen = false;
    let selectedIndex = 0;
    let filteredCommands = [];

    // Provide dynamic username if available, else omit portfolio
    const username = document.body.getAttribute('data-username') || '';

    const allCommands = [
        { id: 'dashboard', title: 'Go to Dashboard', icon: 'layout-dashboard', url: '/dashboard/' },
        { id: 'profile', title: 'Open Profile', icon: 'user', url: '/profile/' },
        { id: 'certificates', title: 'View Certificates', icon: 'award', url: '/certificates/' },
        { id: 'search_courses', title: 'Search Courses', icon: 'search', url: '/courses/' },
        { id: 'create_course', title: 'Create Course (Instructor)', icon: 'plus-square', url: '/instructor/courses/new/' },
    ];
    
    if (username) {
        allCommands.push({ id: 'portfolio', title: 'Open Portfolio', icon: 'briefcase', url: `/profile/portfolio/${username}/` });
    }

    function togglePalette() {
        isOpen = !isOpen;
        palette.style.display = isOpen ? 'flex' : 'none';
        if (isOpen) {
            input.value = '';
            filterCommands('');
            input.focus();
        }
    }

    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            togglePalette();
        }
        if (isOpen && e.key === 'Escape') {
            togglePalette();
        }
        if (isOpen && e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = (selectedIndex + 1) % filteredCommands.length;
            renderCommands();
        }
        if (isOpen && e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = (selectedIndex - 1 + filteredCommands.length) % filteredCommands.length;
            renderCommands();
        }
        if (isOpen && e.key === 'Enter') {
            e.preventDefault();
            if (filteredCommands[selectedIndex]) {
                window.location.href = filteredCommands[selectedIndex].url;
            }
        }
    });

    palette.addEventListener('click', (e) => {
        if (e.target === palette) {
            togglePalette();
        }
    });

    input.addEventListener('input', (e) => {
        filterCommands(e.target.value);
    });

    function filterCommands(query) {
        query = query.toLowerCase();
        filteredCommands = allCommands.filter(c => c.title.toLowerCase().includes(query));
        selectedIndex = 0;
        renderCommands();
    }

    function renderCommands() {
        if (filteredCommands.length === 0) {
            list.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--text-muted); font-size: 0.9rem;">No commands found.</div>`;
            return;
        }

        list.innerHTML = filteredCommands.map((cmd, index) => `
            <a href="${cmd.url}" class="cmd-item ${index === selectedIndex ? 'active' : ''}">
                <div class="cmd-item-icon"><i data-lucide="${cmd.icon}" style="width:18px;"></i></div>
                <div class="cmd-item-title">${cmd.title}</div>
            </a>
        `).join('');
        
        if (window.lucide) window.lucide.createIcons();
    }
});
