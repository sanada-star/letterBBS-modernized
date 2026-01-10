function popup(url) {
    window.open(url, "notice", "width=600,height=450,scrollbars=1");
}

function face(smile) {
    var bbscom = document.bbsform.comment.value;
    document.bbsform.comment.value = bbscom + smile;
}

// Case 1: Floating Form
function openFloatingForm(ownerName) {
    const bbs_cgi = './patio.cgi';

    // Create UI if not exists
    let container = document.getElementById('floating-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'floating-container';
        container.className = 'floating-container';
        container.innerHTML = `
            <div class="floating-header" id="floating-header">
                <span>お手紙を書いています: <span id="floating-target-name"></span></span>
                <div class="floating-close" onclick="closeFloatingForm()">×</div>
            </div>
            <div class="floating-body">
                <iframe id="floating-iframe" name="floating-iframe"></iframe>
            </div>
        `;
        document.body.appendChild(container);
        makeDraggable(container, document.getElementById('floating-header'));
    }

    const iframe = document.getElementById('floating-iframe');
    const targetLabel = document.getElementById('floating-target-name');
    targetLabel.innerText = ownerName + " さん";

    // Find owner thread
    fetch(`${bbs_cgi}?mode=find_owner&name=${encodeURIComponent(ownerName)}`)
        .then(response => response.text())
        .then(data => {
            if (data.startsWith('target_id:')) {
                const threadId = data.split(':')[1];
                iframe.src = `${bbs_cgi}?read=${threadId}&mode=form&view=mini#bbsform`;
                container.style.display = 'flex';
            } else {
                alert(ownerName + " さんの私書箱が見つかりませんでした。先にスレッドを作成していただく必要があるかもしれません。");
            }
        })
        .catch(err => {
            console.error('Error finding owner:', err);
            alert('検索中にエラーが発生しました。');
        });
}

function closeFloatingForm() {
    const container = document.getElementById('floating-container');
    if (container) {
        container.style.display = 'none';
        document.getElementById('floating-iframe').src = 'about:blank';
    }
}

function makeDraggable(el, handle) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    handle.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        el.style.top = (el.offsetTop - pos2) + "px";
        el.style.left = (el.offsetLeft - pos1) + "px";
        el.style.bottom = 'auto';
        el.style.right = 'auto';
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
}

// ========================================
// 文通デスク機能（Correspondesk）
// ========================================

const DESK_STORAGE_KEY = 'letterBBS_correspondesk';

// デスクに置くボタンをクリック
function addToDesk(arg1, arg2) {
    let buttonElement, targetName;

    // 引数のゆらぎ吸収（HTMLが古い場合と新しい場合の両方に対応）
    if (arg1 instanceof HTMLElement) {
        // パターンA: addToDesk(this) - 古いHTML
        buttonElement = arg1;
        targetName = null; // 後でDOMから取得
    } else {
        // パターンB: addToDesk('Name', this) - 新しいHTML
        targetName = arg1;
        buttonElement = arg2;
    }

    if (!buttonElement) return;

    // 親のpostコンテナから入力エリアを探して表示
    const postElement = buttonElement.closest('.post');
    const inputArea = postElement.querySelector('.desk-input-area');

    // targetNameが未取得ならここで取得（フォールバック）
    if (!targetName) {
        const authorBold = postElement.querySelector('.res-author b');
        if (authorBold) targetName = authorBold.innerText.trim();
        else targetName = "名無し"; // 最終手段
    }

    if (inputArea) {
        // Toggle: 既に表示されている場合は閉じる
        if (inputArea.style.display === 'block') {
            inputArea.style.display = 'none';
            return;
        }

        inputArea.style.display = 'block';
        const textarea = inputArea.querySelector('.desk-textarea');

        // タイムライン表示エリアの取得（なければ作る！）
        let timelineContainer = inputArea.querySelector('.desk-timeline');
        if (!timelineContainer) {
            console.log("Creating missing timeline container...");
            timelineContainer = document.createElement('div');
            timelineContainer.className = 'desk-timeline';
            timelineContainer.style.display = 'none'; // 初期は非表示
            // 入力欄(fieldの親または前)の前に挿入
            const firstField = inputArea.querySelector('.desk-field');
            if (firstField) {
                inputArea.insertBefore(timelineContainer, firstField);
            } else {
                inputArea.prepend(timelineContainer);
            }
        }

        if (timelineContainer) {
            timelineContainer.style.display = 'flex'; // 表示
            console.log(`[Timeline] Loading for target: ${targetName}`, postElement);
            loadConversationHistory(targetName, timelineContainer, postElement);
        }

        textarea.focus();
    }
}

// 会話履歴（タイムライン）をロードする
async function loadConversationHistory(targetName, container, currentRefPost) {
    container.innerHTML = '<div class="timeline-loader">会話履歴を読み込んでいます...</div>';

    try {
        const bbs_cgi = './patio.cgi';
        console.log(`[Timeline] Start loading. refPost:`, currentRefPost);

        // 1. 自分の名前（現在のスレッドオーナー）を取得
        // read.html の .post.starter .art-meta から取得する想定
        let myName = "私";
        const metaDiv = document.querySelector('.post.starter .art-meta');
        if (metaDiv) {
            // "投稿者： 名前" という形式を想定してパース
            const text = metaDiv.innerText;
            const match = text.match(/投稿者\s*：\s*(.+)/);
            if (match && match[1]) {
                myName = match[1].trim().split(/\s/)[0]; // 空白区切りで最初の部分だけ取るなどの正規化
            }
        }
        console.log(`[Timeline] Me: ${myName}, Target: ${targetName}`);

        // 2. 現在のページ（自分の箱）から「相手からのメッセージ」を抽出
        // .post (starter & reply) を走査
        const incomingMsgs = [];

        document.querySelectorAll('.post').forEach(post => {
            let authorName = '';
            let dateStr = '';
            let subjectStr = '';
            let cleanText = '';

            // A. Starter Post aka 親記事
            if (post.classList.contains('starter')) {
                // Author & Date finding from .art-meta
                // Format: <div><b>投稿者</b>： 名前</div>
                const metaDivs = post.querySelectorAll('.art-meta div');
                metaDivs.forEach(div => {
                    const text = div.innerText;
                    if (text.includes('投稿者')) {
                        const match = text.match(/投稿者\s*：\s*(.+)/);
                        if (match) authorName = match[1].trim();
                    }
                    if (text.includes('投稿日')) {
                        const match = text.match(/投稿日\s*：\s*(.+)/);
                        if (match) dateStr = match[1].trim().replace(/[()]/g, '');
                    }
                });

                // Subject from .art-head
                // Text often includes icon text if img alt is present, but try to get pure text
                const headEl = post.querySelector('.art-head');
                if (headEl) subjectStr = headEl.innerText.trim();

                // Content
                const commentEl = post.querySelector('.comment');
                if (commentEl) cleanText = commentEl.innerHTML;
            }
            // B. Reply Post
            else {
                const authorEl = post.querySelector('.res-author b');
                const dateEl = post.querySelector('.res-author span');
                const commentEl = post.querySelector('.comment');
                const subEl = post.querySelector('.res-sub');

                if (authorEl) authorName = authorEl.innerText.trim();
                if (dateEl) dateStr = dateEl.innerText.replace(/[()]/g, '');
                if (subEl) subjectStr = subEl.innerText.trim();
                if (commentEl) cleanText = commentEl.innerHTML;
            }

            // Target check
            if (authorName === targetName && cleanText) {
                // 本文のクレンジング
                let finalText = cleanText
                    .split(/<br\s*\/?>/i)
                    .map(line => {
                        let text = line.replace(/<[^>]+>/g, '').trim();
                        if (text.startsWith('&gt;') || text.startsWith('>')) return null;
                        return text;
                    })
                    .filter(line => line !== null && line !== '')
                    .join('<br>');

                if (finalText) {
                    // postが現在の表示場所（container）を含んでいるかチェック（これが確実）
                    const isHere = post.contains(container) || (post === currentRefPost);

                    incomingMsgs.push({
                        type: 'incoming',
                        author: authorName,
                        subject: subjectStr,
                        date: dateStr,
                        text: finalText,
                        rawDate: parseDate(dateStr),
                        isCurrent: isHere
                    });
                }
            }
        });

        // 3. 相手のスレッド（相手の箱）を取得して「自分からのメッセージ」を抽出
        const findResponse = await fetch(`${bbs_cgi}?mode=find_owner&name=${encodeURIComponent(targetName)}`);
        const findData = await findResponse.text();

        const outgoingMsgs = [];

        if (findData.startsWith('target_id:')) {
            const threadId = findData.split(':')[1];
            // 相手のログを取得
            const logResponse = await fetch(`${bbs_cgi}?read=${threadId}&mode=read`);
            const logHtml = await logResponse.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(logHtml, 'text/html');

            doc.querySelectorAll('.post.reply').forEach(post => {
                const authorEl = post.querySelector('.res-author b');
                const dateEl = post.querySelector('.res-author span');
                const commentEl = post.querySelector('.comment');
                const subEl = post.querySelector('.res-sub');

                if (authorEl && authorEl.innerText.trim() === myName) {
                    let dateStr = dateEl ? dateEl.innerText.replace(/[()]/g, '') : '';

                    let rawHtml = commentEl ? commentEl.innerHTML : '';
                    let cleanText = rawHtml
                        .split(/<br\s*\/?>/i)
                        .map(line => {
                            let text = line.replace(/<[^>]+>/g, '').trim();
                            if (text.startsWith('&gt;') || text.startsWith('>')) return null;
                            return text;
                        })
                        .filter(line => line !== null && line !== '')
                        .join('<br>');

                    if (cleanText) {
                        outgoingMsgs.push({
                            type: 'outgoing',
                            author: myName, // 自分
                            subject: subEl ? subEl.innerText.trim() : '',
                            date: dateStr,
                            text: cleanText,
                            rawDate: parseDate(dateStr),
                            isCurrent: false
                        });
                    }
                }
            });
        }

        // 4. マージしてソート
        const allMsgs = [...incomingMsgs, ...outgoingMsgs];

        // 日付で昇順ソート（古い順） -> タイムラインとして読むため
        allMsgs.sort((a, b) => a.rawDate - b.rawDate);

        // 5. 描画
        if (allMsgs.length === 0) {
            container.innerHTML = '<div class="timeline-loader">過去の会話履歴はありません。</div>';
        } else {
            container.innerHTML = '';

            allMsgs.forEach(msg => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'timeline-item' + (msg.isCurrent ? ' timeline-current' : '');

                // 日付整形 (YYYY/MM/DD HH:MM)
                let dateDisplay = msg.date.replace(/\([A-Za-z]+\)/, ''); // 曜日除去

                // ヘッダー（日付と名前）
                const headerDiv = document.createElement('div');
                headerDiv.className = 'timeline-header';

                // 自分の発言か相手の発言かで色を変えるなどの装飾用クラス
                const authorClass = (msg.author === myName) ? 'timeline-author-me' : 'timeline-author-target';

                headerDiv.innerHTML = `
                    <div class="timeline-meta">
                        <span class="timeline-date">${dateDisplay}</span>
                        <span class="timeline-author ${authorClass}">${msg.author}</span>
                    </div>
                    <div class="timeline-subject">${msg.subject}</div>
                `;

                // 本文
                const contentDiv = document.createElement('div');
                contentDiv.className = 'timeline-content';
                contentDiv.innerHTML = msg.text; // クレンジング済みのテキスト(<br>入り)

                // クリックで引用（要望の「引用できるといい」への保険的な対応）
                contentDiv.title = "クリックして引用";
                contentDiv.style.cursor = "pointer";
                contentDiv.onclick = function () {
                    const textarea = container.closest('.desk-input-area').querySelector('.desk-textarea');
                    textarea.value += `> ${msg.text.replace(/<br>/g, '\n> ')}\n`;
                };

                itemDiv.appendChild(headerDiv);
                itemDiv.appendChild(contentDiv);
                container.appendChild(itemDiv);
            });

            // 最新（一番下）へスクロール
            container.scrollTop = container.scrollHeight;
        }

    } catch (e) {
        console.error(e);
        container.innerHTML = '<div class="timeline-loader">履歴の読み込みに失敗しました。</div>';
    }
}

// 日付文字列をDateオブジェクトに変換するヘルパー（強化版：秒対応）
function parseDate(str) {
    if (!str) return 0;
    // 数値だけ取り出して処理する (2026/01/09(Fri) 15:10:05 -> 2026, 1, 9, 15, 10, 5)
    // 古い形式 (2026/01/09(Fri) 15:10) にも対応できるよう、秒部分は任意(?:...)?にする
    const match = str.match(/(\d{4})[\/-](\d{1,2})[\/-](\d{1,2}).*?(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?/);
    if (match) {
        const year = parseInt(match[1], 10);
        const month = parseInt(match[2], 10) - 1; // 月は0始まり
        const day = parseInt(match[3], 10);
        const hour = parseInt(match[4], 10);
        const min = parseInt(match[5], 10);
        const sec = match[6] ? parseInt(match[6], 10) : 0; // 秒がなければ0
        return new Date(year, month, day, hour, min, sec).getTime();
    }
    // フォールバック
    return Date.parse(str) || 0;
}

// 入力エリアを閉じる
function closeDeskInput(buttonElement) {
    const inputArea = buttonElement.closest('.desk-input-area');
    if (inputArea) {
        inputArea.style.display = 'none';
        inputArea.querySelector('.desk-subject').value = '';
        inputArea.querySelector('.desk-name').value = '';
        inputArea.querySelector('.desk-pwd').value = '';
        inputArea.querySelector('.desk-textarea').value = '';
        // タイムラインもクリアしておく（次回開くときに再ロード）
        const timeline = inputArea.querySelector('.desk-timeline');
        if (timeline) timeline.innerHTML = '';
    }
}

// お返事をlocalStorageに保存
function saveToDeskStorage(targetName, buttonElement) {
    const inputArea = buttonElement.closest('.desk-input-area');
    const subject = inputArea.querySelector('.desk-subject').value.trim();
    const name = inputArea.querySelector('.desk-name').value.trim();
    const pwd = inputArea.querySelector('.desk-pwd').value.trim();
    const textarea = inputArea.querySelector('.desk-textarea');
    const message = textarea.value.trim();

    if (!subject) {
        alert('件名を入力してください。');
        return;
    }
    if (!name) {
        alert('あなたの名前を入力してください。');
        return;
    }
    if (!pwd) {
        alert('パスワードを入力してください。');
        return;
    }
    if (!message) {
        alert('お返事の内容を入力してください。');
        return;
    }

    // 既存のストックを取得
    let deskItems = JSON.parse(localStorage.getItem(DESK_STORAGE_KEY) || '[]');

    // 同じ宛先が既にある場合は上書き
    const existingIndex = deskItems.findIndex(item => item.targetName === targetName);
    if (existingIndex >= 0) {
        deskItems[existingIndex].subject = subject;
        deskItems[existingIndex].name = name;
        deskItems[existingIndex].pwd = pwd;
        deskItems[existingIndex].message = message;
        deskItems[existingIndex].timestamp = new Date().toISOString();
    } else {
        deskItems.push({
            targetName: targetName,
            subject: subject,
            name: name,
            pwd: pwd,
            message: message,
            timestamp: new Date().toISOString()
        });
    }

    localStorage.setItem(DESK_STORAGE_KEY, JSON.stringify(deskItems));

    // 入力エリアを閉じる
    closeDeskInput(buttonElement);

    // デスクパネルを更新
    refreshDeskPanel();

    alert(`${targetName} さんへのお返事を文通デスクに保存しました！`);
}

// デスクパネルを更新
function refreshDeskPanel() {
    const deskItems = JSON.parse(localStorage.getItem(DESK_STORAGE_KEY) || '[]');
    const listContainer = document.getElementById('deskItemList');
    const emptyMsg = document.getElementById('deskEmptyMsg');

    if (deskItems.length === 0) {
        listContainer.innerHTML = '';
        emptyMsg.style.display = 'block';
        return;
    }

    emptyMsg.style.display = 'none';
    listContainer.innerHTML = deskItems.map((item, index) => `
        <div class="desk-item">
            <div class="desk-item-header">
                <div>
                    <strong>宛先: ${item.targetName}</strong>
                    <div class="desk-item-meta">件名: ${item.subject || '(未設定)'} / 投稿者: ${item.name || '(未設定)'}</div>
                </div>
                <button onclick="removeDeskItem(${index})" class="btn-remove-item">削除</button>
            </div>
            <div class="desk-item-message">${item.message.replace(/\n/g, '<br>')}</div>
            <div class="desk-item-footer">
                <small>${new Date(item.timestamp).toLocaleString('ja-JP')}</small>
            </div>
        </div>
    `).join('');
}

// 個別のアイテムを削除
function removeDeskItem(index) {
    let deskItems = JSON.parse(localStorage.getItem(DESK_STORAGE_KEY) || '[]');
    deskItems.splice(index, 1);
    localStorage.setItem(DESK_STORAGE_KEY, JSON.stringify(deskItems));
    refreshDeskPanel();
}

// 全てクリア
function clearAllDeskItems() {
    if (confirm('文通デスクの全てのお返事を削除しますか？')) {
        localStorage.removeItem(DESK_STORAGE_KEY);
        refreshDeskPanel();
    }
}

// デスクパネルの開閉
function toggleDeskPanel() {
    const panel = document.getElementById('correspondeskPanel');
    const content = panel.querySelector('.desk-content');
    const toggleBtn = panel.querySelector('.btn-toggle-desk');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggleBtn.textContent = '▼';
    } else {
        content.style.display = 'none';
        toggleBtn.textContent = '▲';
    }
}

// ページ読み込み時にデスクパネルを初期化
document.addEventListener('DOMContentLoaded', function () {
    const panel = document.getElementById('correspondeskPanel');
    if (panel) {
        refreshDeskPanel();
    }
});

// ========================================
// フェーズ2：一括自動送信機能
// ========================================

// 一括送信
async function sendAllDeskItems() {
    const deskItems = JSON.parse(localStorage.getItem(DESK_STORAGE_KEY) || '[]');

    if (deskItems.length === 0) {
        alert('送信するお返事がありません。');
        return;
    }

    if (!confirm(`${deskItems.length}件のお返事を一括送信しますか？`)) {
        return;
    }

    const bbs_cgi = './patio.cgi';
    const regist_cgi = './regist.cgi';
    let successCount = 0;
    let failedItems = [];

    // プログレス表示用
    const panel = document.getElementById('correspondeskPanel');
    const originalContent = panel.querySelector('.desk-content').innerHTML;
    panel.querySelector('.desk-content').innerHTML = '<div class="desk-progress">送信中...</div>';

    for (let i = 0; i < deskItems.length; i++) {
        const item = deskItems[i];
        panel.querySelector('.desk-progress').textContent = `送信中... (${i + 1}/${deskItems.length}) ${item.targetName}さんへ`;

        try {
            // 1. スレッドIDを検索
            const findResponse = await fetch(`${bbs_cgi}?mode=find_owner&name=${encodeURIComponent(item.targetName)}`);
            const findData = await findResponse.text();

            if (!findData.startsWith('target_id:')) {
                failedItems.push({ name: item.targetName, reason: '私書箱が見つかりませんでした' });
                continue;
            }

            const threadId = findData.split(':')[1];

            // 2. regist.cgiへPOST
            const formData = new FormData();
            formData.append('mode', 'regist');
            formData.append('res', threadId);  // 重要：返信モード
            formData.append('sort', '1');      // スレッドをトップへ上げる
            formData.append('sub', item.subject);
            formData.append('name', item.name);
            formData.append('pwd', item.pwd);
            formData.append('comment', item.message);

            const postResponse = await fetch(regist_cgi, {
                method: 'POST',
                body: formData
            });

            if (postResponse.ok) {
                successCount++;
            } else {
                failedItems.push({ name: item.targetName, reason: '投稿に失敗しました' });
            }

            // サーバー負荷軽減のため少し待機
            await new Promise(resolve => setTimeout(resolve, 500));

        } catch (error) {
            failedItems.push({ name: item.targetName, reason: 'エラー: ' + error.message });
        }
    }

    // 結果表示
    let resultMessage = `送信完了！\n成功: ${successCount}件`;
    if (failedItems.length > 0) {
        resultMessage += `\n失敗: ${failedItems.length}件\n\n`;
        resultMessage += failedItems.map(f => `・${f.name}: ${f.reason}`).join('\n');
    }

    alert(resultMessage);

    // 成功したものだけデスクから削除
    if (successCount > 0) {
        let remainingItems = [];
        for (let i = 0; i < deskItems.length; i++) {
            const item = deskItems[i];
            const failed = failedItems.find(f => f.name === item.targetName);
            if (failed) {
                remainingItems.push(item);
            }
        }
        localStorage.setItem(DESK_STORAGE_KEY, JSON.stringify(remainingItems));
    }

    // パネルを更新
    panel.querySelector('.desk-content').innerHTML = originalContent;
    refreshDeskPanel();
}
// ========================================
// Resident Notification System (Phase 8)
// ========================================
// ========================================
// Resident Notification System (Phase 8 - Task Style)
// ========================================
const NOTIFY_KEY_NAME = 'letterBBS_notify_name';
const NOTIFY_KEY_STATE = 'letterBBS_notify_state'; // ON/OFF
const NOTIFY_KEY_LAST = 'letterBBS_notify_last'; // Last Snapshot {thID: count}
const NOTIFY_KEY_UNREAD = 'letterBBS_notify_unread'; // Unread Queue [{sub, author, id...}]

const NotificationSystem = {
    intervalId: null,
    monitorName: '',
    isEnabled: false,

    init: function () {
        // Load Settings
        this.monitorName = localStorage.getItem(NOTIFY_KEY_NAME) || '';
        this.isEnabled = (localStorage.getItem(NOTIFY_KEY_STATE) === 'true');

        // Create UI
        this.createUI();

        // Check for unread items on load and show them
        this.checkUnreadOnLoad();

        // Start if enabled
        if (this.isEnabled && this.monitorName) {
            this.start();
        }
    },

    createUI: function () {
        // Add Bell Icon to Header or Menu
        const menu = document.querySelector('#menu');
        if (menu) {
            const btn = document.createElement('a');
            btn.href = "javascript:void(0)";
            btn.className = "menu-notify";
            btn.innerHTML = `<span id="notify-icon">${this.isEnabled ? '🔔' : '🔕'}</span> 通知設定`;
            btn.onclick = () => this.openSettings();
            menu.appendChild(btn);
        }
    },

    openSettings: function () {
        const currentName = this.monitorName;
        const currentState = this.isEnabled;

        const newName = prompt("【通知設定】\n監視する「あなたの名前」を入力してください。\n(この名前のスレッドに動きがあると通知されます)", currentName);

        if (newName === null) return; // Cancel

        let newState = currentState;
        if (newName) {
            newState = confirm("通知機能をONにしますか？\n(OK=ON / キャンセル=OFF)");
        } else {
            alert("名前が設定されていないため、通知機能はOFFになります。");
            newState = false;
        }

        // Save
        this.monitorName = newName.trim();
        this.isEnabled = newState;
        localStorage.setItem(NOTIFY_KEY_NAME, this.monitorName);
        localStorage.setItem(NOTIFY_KEY_STATE, this.isEnabled);

        // Update UI
        const icon = document.getElementById('notify-icon');
        if (icon) icon.innerText = this.isEnabled ? '🔔' : '🔕';

        // Toggle Process
        if (this.isEnabled && this.monitorName) {
            this.requestPermission();
            this.start();
            alert("通知の監視を開始しました。\nこのタブを開いたままにしておいてください。\n(10秒ごとに更新チェックを行います)");
        } else {
            this.stop();
            alert("監視を停止しました。\n(未読タスクは残ります)");
        }
    },

    requestPermission: function () {
        if (!("Notification" in window)) {
            alert("このブラウザはデスクトップ通知に対応していません。");
            return;
        }
        if (Notification.permission !== "denied") {
            Notification.requestPermission();
        }
    },

    start: function () {
        if (this.intervalId) clearInterval(this.intervalId);
        // First check immediately
        this.checkValues();
        // Loop every 10s
        this.intervalId = setInterval(() => this.checkValues(), 10000);
        console.log("Notification Monitor Started (10s)");
    },

    stop: function () {
        if (this.intervalId) clearInterval(this.intervalId);
        this.intervalId = null;
        console.log("Notification Monitor Stopped");
    },

    checkValues: async function () {
        if (!this.monitorName) return;

        // Visual Heartbeat
        const icon = document.getElementById('notify-icon');
        if (icon) {
            icon.style.transition = 'transform 0.5s';
            icon.style.transform = 'rotate(360deg)';
            setTimeout(() => { icon.style.transform = 'rotate(0deg)'; }, 500);
        }

        try {
            const res = await fetch('./patio.cgi?mode=api_list&t=' + Date.now(), { cache: "no-store" });
            const list = await res.json();

            const lastSnapshot = JSON.parse(localStorage.getItem(NOTIFY_KEY_LAST) || '{}');
            const newSnapshot = {};

            // 1. Find My Thread & Check Updates
            const myThreads = list.filter(item => item.name === this.monitorName);

            myThreads.forEach(thread => {
                const currentRes = parseInt(thread.res, 10);
                newSnapshot[thread.id] = currentRes;

                const oldRes = lastSnapshot[thread.id];

                // Compare
                if (oldRes !== undefined && currentRes > parseInt(oldRes, 10)) {
                    // NEW POST DETECTED!
                    const oldResInt = parseInt(oldRes, 10);
                    const diff = currentRes - oldResInt;
                    this.addUnread(thread.sub, thread.last_name, thread.id, diff);
                }
            });

            localStorage.setItem(NOTIFY_KEY_LAST, JSON.stringify(newSnapshot));

        } catch (e) {
            console.error("Monitor Check Failed", e);
        }
    },

    // Add unread item to queue and notify
    addUnread: function (sub, author, id, diff) {
        let unread = JSON.parse(localStorage.getItem(NOTIFY_KEY_UNREAD) || '[]');

        // Use diff (new replies count) or default to 1
        const newCount = diff || 1;

        const idx = unread.findIndex(u => u.id === id);

        if (idx >= 0) {
            // Update existing task
            unread[idx].timestamp = Date.now();
            unread[idx].author = author; // Update latest author
            unread[idx].count = (unread[idx].count || 0) + newCount; // Increment count
        } else {
            // New task
            unread.push({
                id: id,
                sub: sub,
                author: author,
                timestamp: Date.now(),
                count: newCount
            });
        }

        localStorage.setItem(NOTIFY_KEY_UNREAD, JSON.stringify(unread));

        // Trigger generic notification
        this.triggerNotify(sub, author, newCount);

        // Update Toast UI
        this.updateToastUI();
    },

    triggerNotify: function (threadTitle, lastAuthor, count) {
        const msg = `${lastAuthor} さんからのお手紙が届きました！` + (count > 1 ? ` (+${count}件)` : '') + `\n件名: ${threadTitle}`;
        const tag = "letterbbs-" + Date.now();

        // 1. Browser Notification (Transient)
        if (Notification.permission === "granted") {
            try {
                new Notification("LetterBBS: 新着あり", {
                    body: msg,
                    icon: "./cmn/icon/fld_bell.gif",
                    tag: tag
                });
            } catch (e) { }
        }
    },

    // Check localStorage on load
    checkUnreadOnLoad: function () {
        this.updateToastUI();
    },

    // Clear specific item
    clearUnread: function (id) {
        let unread = JSON.parse(localStorage.getItem(NOTIFY_KEY_UNREAD) || '[]');
        unread = unread.filter(u => u.id !== id);
        localStorage.setItem(NOTIFY_KEY_UNREAD, JSON.stringify(unread));
        this.updateToastUI();
    },

    // Show persistent Toast
    updateToastUI: function () {
        let unread = JSON.parse(localStorage.getItem(NOTIFY_KEY_UNREAD) || '[]');
        let toast = document.getElementById('notify-toast');

        if (unread.length === 0) {
            if (toast) toast.style.transform = 'translateX(120%)';
            return;
        }

        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'notify-toast';
            // Styling for "Todo List" mode
            toast.style.cssText = `
                position: fixed; top: 20px; right: 20px;
                background: rgba(40, 44, 52, 0.95); color: #fff;
                padding: 0; border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.4);
                z-index: 9999; font-size: 0.9rem;
                transform: translateX(120%); transition: transform 0.3s ease;
                min-width: 250px; max-width: 320px;
                overflow: hidden;
            `;
            document.body.appendChild(toast);
        }

        // Header
        let html = `
            <div style="background:#ff4757; padding:10px 15px; font-weight:bold; display:flex; justify-content:space-between; align-items:center;">
                <span>📮 未読のお手紙</span>
                <span style="font-size:0.8em; cursor:pointer;" onclick="document.getElementById('notify-toast').style.transform='translateX(120%)'">▼</span>
            </div>
            <div style="padding:10px; max-height:300px; overflow-y:auto;">
        `;

        // List Items
        unread.forEach(u => {
            html += `
                <div style="background:rgba(255,255,255,0.1); margin-bottom:8px; padding:10px; border-radius:4px; border-left:3px solid #ff4757; position:relative;">
                    <div style="font-size:0.85em; color:#ccc;">${new Date(u.timestamp).toLocaleTimeString()} / From: ${u.author}</div>
                    <div style="font-weight:bold; margin:3px 0;">${u.sub}</div>
                    <a href="./patio.cgi?read=${u.id}&ukey=0" target="_blank" style="color:#61dafb; font-size:0.9em; text-decoration:underline;">返信しに行く</a>
                    <button onclick="NotificationSystem.clearUnread('${u.id}')" style="display:block; width:100%; margin-top:5px; border:none; background:#777; color:#fff; padding:4px; border-radius:2px; cursor:pointer;">× 完了（通知を消す）</button>
                </div>
            `;
        });

        html += `</div>`;
        toast.innerHTML = html;

        // Show
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        // NO Auto-hide here
    }
};

// Start
document.addEventListener('DOMContentLoaded', function () {
    NotificationSystem.init();
});
