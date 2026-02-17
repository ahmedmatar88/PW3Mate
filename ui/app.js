/* ------------------------------------------------------------------ */
/*  PW3Mate – Schedule Manager UI (vanilla JS)                        */
/* ------------------------------------------------------------------ */

(function () {
    'use strict';

    // ------------------------------------------------------------------
    //  CONFIGURATION – set this to your API Gateway invoke URL
    //  e.g. "https://abc123.execute-api.eu-west-1.amazonaws.com/prod"
    // ------------------------------------------------------------------
    const API_BASE = window.PW3_API_BASE || '';

    // ------------------------------------------------------------------
    //  State
    // ------------------------------------------------------------------
    let authToken = sessionStorage.getItem('pw3_token') || '';
    let schedules = [];
    let deleteTarget = null; // rule_name queued for deletion

    // ------------------------------------------------------------------
    //  DOM refs
    // ------------------------------------------------------------------
    const $loginScreen   = document.getElementById('login-screen');
    const $dashboard     = document.getElementById('dashboard');
    const $loginForm     = document.getElementById('login-form');
    const $loginError    = document.getElementById('login-error');
    const $logoutBtn     = document.getElementById('logout-btn');
    const $addBtn        = document.getElementById('add-schedule-btn');
    const $schedulesList = document.getElementById('schedules-list');
    const $emptyState    = document.getElementById('empty-state');
    const $loading       = document.getElementById('loading');
    const $tzLabel       = document.getElementById('timezone-label');

    // Modal refs
    const $modal         = document.getElementById('schedule-modal');
    const $modalTitle    = document.getElementById('modal-title');
    const $modalForm     = document.getElementById('schedule-form');
    const $modalHour     = document.getElementById('schedule-hour');
    const $modalMinute   = document.getElementById('schedule-minute');
    const $modalPct      = document.getElementById('schedule-percentage');
    const $pctDisplay    = document.getElementById('percentage-display');
    const $editingRule   = document.getElementById('editing-rule-name');
    const $localPreview  = document.getElementById('local-time-preview');

    const $deleteModal   = document.getElementById('delete-modal');
    const $deleteMsg     = document.getElementById('delete-message');

    // ------------------------------------------------------------------
    //  Init
    // ------------------------------------------------------------------
    function init() {
        populateTimeSelects();
        bindEvents();

        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        $tzLabel.textContent = 'Times shown in your local timezone (' + tz + ')';

        if (authToken) {
            showDashboard();
        } else {
            showLogin();
        }
    }

    // ------------------------------------------------------------------
    //  API helpers
    // ------------------------------------------------------------------
    function api(method, path, body) {
        const opts = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (authToken) opts.headers['Authorization'] = 'Bearer ' + authToken;
        if (body) opts.body = JSON.stringify(body);

        return fetch(API_BASE + path, opts).then(function (res) {
            return res.json().then(function (data) {
                if (res.status === 401) {
                    logout();
                    throw new Error('Session expired');
                }
                if (!res.ok) throw new Error(data.error || 'Request failed');
                return data;
            });
        });
    }

    // ------------------------------------------------------------------
    //  Auth
    // ------------------------------------------------------------------
    function showLogin() {
        $loginScreen.classList.remove('hidden');
        $dashboard.classList.add('hidden');
    }

    function showDashboard() {
        $loginScreen.classList.add('hidden');
        $dashboard.classList.remove('hidden');
        loadSchedules();
    }

    function logout() {
        authToken = '';
        sessionStorage.removeItem('pw3_token');
        showLogin();
    }

    // ------------------------------------------------------------------
    //  Schedules
    // ------------------------------------------------------------------
    function loadSchedules() {
        $loading.classList.remove('hidden');
        $schedulesList.classList.add('hidden');
        $emptyState.classList.add('hidden');

        api('GET', '/api/schedules')
            .then(function (data) {
                schedules = data.schedules || [];
                renderSchedules();
            })
            .catch(function (err) {
                toast('Failed to load schedules: ' + err.message, 'error');
            })
            .finally(function () {
                $loading.classList.add('hidden');
            });
    }

    function renderSchedules() {
        $schedulesList.innerHTML = '';

        if (schedules.length === 0) {
            $emptyState.classList.remove('hidden');
            $schedulesList.classList.add('hidden');
            return;
        }

        $emptyState.classList.add('hidden');
        $schedulesList.classList.remove('hidden');

        schedules.forEach(function (s) {
            $schedulesList.appendChild(buildCard(s));
        });
    }

    function buildCard(s) {
        var card = document.createElement('div');
        card.className = 'schedule-card' + (s.enabled ? '' : ' disabled');

        var utcStr = pad(s.hour) + ':' + pad(s.minute) + ' UTC';
        var localStr = utcToLocal(s.hour, s.minute);
        var pct = s.percentage != null ? s.percentage : 0;
        var barColor = percentageColor(pct);

        card.innerHTML =
            '<div class="card-top">' +
                '<div>' +
                    '<div class="card-time">' + localStr + '</div>' +
                    '<div class="card-time-local">' + utcStr + '</div>' +
                '</div>' +
                '<div class="card-actions">' +
                    '<button class="btn-icon" data-action="edit" data-rule="' + esc(s.rule_name) + '" title="Edit">&#9998;</button>' +
                    '<button class="btn-icon" data-action="delete" data-rule="' + esc(s.rule_name) + '" title="Delete">&#128465;</button>' +
                '</div>' +
            '</div>' +
            '<div class="card-percentage">' +
                '<div class="percentage-bar-bg">' +
                    '<div class="percentage-bar" style="width:' + pct + '%;background:' + barColor + '"></div>' +
                '</div>' +
                '<div class="percentage-value">' + pct + '%</div>' +
            '</div>' +
            '<div class="card-footer">' +
                '<span class="card-label">' + (s.enabled ? 'Active' : 'Paused') + '</span>' +
                '<label class="toggle">' +
                    '<input type="checkbox"' + (s.enabled ? ' checked' : '') + ' data-action="toggle" data-rule="' + esc(s.rule_name) + '">' +
                    '<span class="toggle-slider"></span>' +
                '</label>' +
            '</div>';

        return card;
    }

    // ------------------------------------------------------------------
    //  Card actions (delegated)
    // ------------------------------------------------------------------
    function handleCardAction(e) {
        var target = e.target.closest('[data-action]');
        if (!target) return;

        var action = target.getAttribute('data-action');
        var ruleName = target.getAttribute('data-rule');

        if (action === 'edit') {
            var s = schedules.find(function (x) { return x.rule_name === ruleName; });
            if (s) openEditModal(s);
        } else if (action === 'delete') {
            var sd = schedules.find(function (x) { return x.rule_name === ruleName; });
            openDeleteModal(sd);
        } else if (action === 'toggle') {
            toggleSchedule(ruleName, target.checked);
        }
    }

    function toggleSchedule(ruleName, enabled) {
        api('PUT', '/api/schedules', { rule_name: ruleName, enabled: enabled })
            .then(function () {
                toast(enabled ? 'Schedule enabled' : 'Schedule paused', 'success');
                loadSchedules();
            })
            .catch(function (err) {
                toast('Failed to update: ' + err.message, 'error');
                loadSchedules();
            });
    }

    // ------------------------------------------------------------------
    //  Add / Edit modal
    // ------------------------------------------------------------------
    function openAddModal() {
        $modalTitle.textContent = 'Add Schedule';
        $modalHour.value = '12';
        $modalMinute.value = '0';
        $modalPct.value = '50';
        $pctDisplay.textContent = '50';
        $editingRule.value = '';
        updateLocalPreview();
        $modal.classList.remove('hidden');
    }

    function openEditModal(s) {
        $modalTitle.textContent = 'Edit Schedule';
        $modalHour.value = String(s.hour);
        $modalMinute.value = String(s.minute);
        $modalPct.value = String(s.percentage || 0);
        $pctDisplay.textContent = String(s.percentage || 0);
        $editingRule.value = s.rule_name;
        updateLocalPreview();
        $modal.classList.remove('hidden');
    }

    function closeModal() { $modal.classList.add('hidden'); }

    function saveSchedule(e) {
        e.preventDefault();
        var hour = parseInt($modalHour.value, 10);
        var minute = parseInt($modalMinute.value, 10);
        var percentage = parseInt($modalPct.value, 10);
        var existingRule = $editingRule.value;

        var payload = { hour: hour, minute: minute, percentage: percentage };

        if (existingRule) {
            payload.rule_name = existingRule;
            payload.enabled = true;
            api('PUT', '/api/schedules', payload)
                .then(function () { toast('Schedule updated', 'success'); closeModal(); loadSchedules(); })
                .catch(function (err) { toast('Failed to update: ' + err.message, 'error'); });
        } else {
            api('POST', '/api/schedules', payload)
                .then(function () { toast('Schedule created', 'success'); closeModal(); loadSchedules(); })
                .catch(function (err) { toast('Failed to create: ' + err.message, 'error'); });
        }
    }

    // ------------------------------------------------------------------
    //  Delete modal
    // ------------------------------------------------------------------
    function openDeleteModal(s) {
        if (!s) return;
        deleteTarget = s.rule_name;
        var localStr = utcToLocal(s.hour, s.minute);
        $deleteMsg.textContent = 'Delete the ' + localStr + ' \u2192 ' + s.percentage + '% schedule?';
        $deleteModal.classList.remove('hidden');
    }

    function closeDeleteModal() { $deleteModal.classList.add('hidden'); deleteTarget = null; }

    function confirmDelete() {
        if (!deleteTarget) return;
        api('DELETE', '/api/schedules', { rule_name: deleteTarget })
            .then(function () { toast('Schedule deleted', 'success'); closeDeleteModal(); loadSchedules(); })
            .catch(function (err) { toast('Failed to delete: ' + err.message, 'error'); });
    }

    // ------------------------------------------------------------------
    //  Time helpers
    // ------------------------------------------------------------------
    function populateTimeSelects() {
        var i;
        for (i = 0; i < 24; i++) {
            var opt = document.createElement('option');
            opt.value = String(i);
            opt.textContent = pad(i);
            $modalHour.appendChild(opt);
        }
        for (i = 0; i < 60; i++) {
            var opt2 = document.createElement('option');
            opt2.value = String(i);
            opt2.textContent = pad(i);
            $modalMinute.appendChild(opt2);
        }
    }

    function utcToLocal(hour, minute) {
        // Build a UTC date for today with the given hour/minute, then format in local tz
        var d = new Date();
        d.setUTCHours(hour, minute, 0, 0);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    }

    function updateLocalPreview() {
        var h = parseInt($modalHour.value, 10);
        var m = parseInt($modalMinute.value, 10);
        $localPreview.textContent = 'Your local time: ' + utcToLocal(h, m);
    }

    function pad(n) { return n < 10 ? '0' + n : String(n); }

    // ------------------------------------------------------------------
    //  UI helpers
    // ------------------------------------------------------------------
    function percentageColor(pct) {
        if (pct >= 80) return '#10b981';
        if (pct >= 40) return '#f59e0b';
        if (pct > 0)  return '#ef4444';
        return '#94a3b8';
    }

    function esc(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str || ''));
        return div.innerHTML;
    }

    function toast(msg, type) {
        var el = document.createElement('div');
        el.className = 'toast toast-' + (type || 'success');
        el.textContent = msg;
        document.getElementById('toast-container').appendChild(el);
        setTimeout(function () { el.remove(); }, 3500);
    }

    // ------------------------------------------------------------------
    //  Event binding
    // ------------------------------------------------------------------
    function bindEvents() {
        // Login
        $loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            $loginError.classList.add('hidden');
            var pw = document.getElementById('password').value;

            api('POST', '/api/login', { password: pw })
                .then(function (data) {
                    authToken = data.token;
                    sessionStorage.setItem('pw3_token', authToken);
                    document.getElementById('password').value = '';
                    showDashboard();
                })
                .catch(function (err) {
                    $loginError.textContent = err.message || 'Login failed';
                    $loginError.classList.remove('hidden');
                });
        });

        $logoutBtn.addEventListener('click', logout);

        // Dashboard
        $addBtn.addEventListener('click', openAddModal);
        $schedulesList.addEventListener('click', handleCardAction);
        $schedulesList.addEventListener('change', handleCardAction);

        // Add/Edit modal
        $modalForm.addEventListener('submit', saveSchedule);
        $modalPct.addEventListener('input', function () { $pctDisplay.textContent = this.value; });
        $modalHour.addEventListener('change', updateLocalPreview);
        $modalMinute.addEventListener('change', updateLocalPreview);
        document.getElementById('modal-cancel').addEventListener('click', closeModal);
        $modal.querySelector('.modal-close').addEventListener('click', closeModal);
        $modal.querySelector('.modal-backdrop').addEventListener('click', closeModal);

        // Delete modal
        document.getElementById('delete-cancel').addEventListener('click', closeDeleteModal);
        document.getElementById('delete-confirm').addEventListener('click', confirmDelete);
        $deleteModal.querySelector('.modal-close').addEventListener('click', closeDeleteModal);
        $deleteModal.querySelector('.modal-backdrop').addEventListener('click', closeDeleteModal);
    }

    // ------------------------------------------------------------------
    //  Boot
    // ------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', init);
})();
