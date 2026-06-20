document.addEventListener('DOMContentLoaded', () => {
    const bellBtn = document.getElementById('notificationBell');
    const dropdown = document.getElementById('notificationDropdown');
    const list = document.getElementById('notificationList');
    const countSpan = document.getElementById('unreadCount');
    const markReadBtn = document.getElementById('markAllReadBtn');

    if (!bellBtn) return;

    let dropdownOpen = false;

    // Fetch initial count
    fetchNotifications(true);

    bellBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownOpen = !dropdownOpen;
        dropdown.style.display = dropdownOpen ? 'flex' : 'none';
        
        if (dropdownOpen) {
            renderSkeletons();
            fetchNotifications(false);
        }
    });

    document.addEventListener('click', (e) => {
        if (dropdownOpen && !dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
            dropdown.style.display = 'none';
            dropdownOpen = false;
        }
    });

    markReadBtn.addEventListener('click', () => {
        fetch('/notifications/api/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        }).then(res => res.json()).then(data => {
            if (data.status === 'success') {
                countSpan.style.display = 'none';
                countSpan.innerText = '0';
                fetchNotifications(false);
            }
        });
    });

    function renderSkeletons() {
        list.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            list.innerHTML += `
                <div style="display: flex; gap: 10px; align-items: flex-start; padding: 10px; border-radius: 8px; background: rgba(0,0,0,0.02);">
                    <div class="skeleton skeleton-avatar" style="width: 32px; height: 32px;"></div>
                    <div style="flex: 1;">
                        <div class="skeleton skeleton-text" style="width: 80%; height: 14px; margin-bottom: 8px;"></div>
                        <div class="skeleton skeleton-text" style="width: 60%; height: 12px;"></div>
                    </div>
                </div>
            `;
        }
    }

    function fetchNotifications(onlyCount = false) {
        fetch('/notifications/api/recent/')
            .then(res => res.json())
            .then(data => {
                const unreadCount = data.unread_count;
                if (unreadCount > 0) {
                    countSpan.style.display = 'block';
                    countSpan.innerText = unreadCount > 9 ? '9+' : unreadCount;
                } else {
                    countSpan.style.display = 'none';
                }

                if (!onlyCount) {
                    renderNotifications(data.notifications);
                }
            })
            .catch(err => {
                console.error(err);
                if (!onlyCount) list.innerHTML = '<p style="text-align:center;font-size:0.85rem;color:var(--text-muted);">Failed to load notifications.</p>';
            });
    }

    function renderNotifications(notifications) {
        if (notifications.length === 0) {
            list.innerHTML = `
                <div class="empty-state" style="padding: 1rem 0;">
                    <i data-lucide="bell-off" style="width:32px; color:var(--border);"></i>
                    <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.5rem;">No recent notifications</p>
                </div>
            `;
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        list.innerHTML = '';
        notifications.forEach(notif => {
            let bg = notif.is_read ? 'transparent' : 'rgba(37, 99, 235, 0.05)';
            let icon = getIconForType(notif.type);
            
            let html = `
                <a href="${notif.link || '#'}" style="text-decoration:none; color:inherit; display:flex; gap:10px; align-items:flex-start; padding:10px; border-radius:8px; background:${bg}; transition: background 0.2s;">
                    <div style="width:32px; height:32px; border-radius:16px; background:var(--card-bg); border:1px solid var(--border); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                        <i data-lucide="${icon}" style="width:16px; color:var(--accent-primary);"></i>
                    </div>
                    <div>
                        <div style="font-size:0.85rem; font-weight:600; color:var(--text-primary); margin-bottom:2px;">${notif.title}</div>
                        <div style="font-size:0.8rem; color:var(--text-muted); line-height:1.4;">${notif.message}</div>
                        <div style="font-size:0.7rem; color:var(--text-muted); margin-top:4px;">${notif.created_at}</div>
                    </div>
                </a>
            `;
            list.innerHTML += html;
        });

        if (window.lucide) window.lucide.createIcons();
    }

    function getIconForType(type) {
        switch(type) {
            case 'ACHIEVEMENT': return 'award';
            case 'CERTIFICATE': return 'file-badge-2';
            case 'MILESTONE': return 'target';
            case 'DISCUSSION_REPLY': return 'message-circle';
            case 'PROJECT_RECOGNITION': return 'star';
            default: return 'bell';
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
