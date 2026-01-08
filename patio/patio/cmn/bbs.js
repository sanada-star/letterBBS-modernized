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
function addToDesk(targetName, buttonElement) {
    // 親のpostコンテナから入力エリアを探して表示
    const postElement = buttonElement.closest('.post');
    const inputArea = postElement.querySelector('.desk-input-area');
    if (inputArea) {
        inputArea.style.display = 'block';
        const textarea = inputArea.querySelector('.desk-textarea');
        textarea.focus();
    }
}

// 入力エリアを閉じる
function closeDeskInput(buttonElement) {
    const inputArea = buttonElement.closest('.desk-input-area');
    if (inputArea) {
        inputArea.style.display = 'none';
        const textarea = inputArea.querySelector('.desk-textarea');
        textarea.value = '';
    }
}

// お返事をlocalStorageに保存
function saveToDeskStorage(targetName, buttonElement) {
    const inputArea = buttonElement.closest('.desk-input-area');
    const textarea = inputArea.querySelector('.desk-textarea');
    const message = textarea.value.trim();

    if (!message) {
        alert('お返事の内容を入力してください。');
        return;
    }

    // 既存のストックを取得
    let deskItems = JSON.parse(localStorage.getItem(DESK_STORAGE_KEY) || '[]');

    // 同じ宛先が既にある場合は上書き
    const existingIndex = deskItems.findIndex(item => item.targetName === targetName);
    if (existingIndex >= 0) {
        deskItems[existingIndex].message = message;
        deskItems[existingIndex].timestamp = new Date().toISOString();
    } else {
        deskItems.push({
            targetName: targetName,
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
                <strong>宛先: ${item.targetName}</strong>
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
