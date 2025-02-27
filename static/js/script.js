/**
 * Hue照明コントローラー JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // 照明スイッチの制御
    const lightSwitches = document.querySelectorAll('.light-switch');
    lightSwitches.forEach(switchEl => {
        switchEl.addEventListener('change', function() {
            const lightId = this.dataset.lightId;
            const isOn = this.checked;
            
            // 照明カードのスタイルを更新
            const lightCard = document.querySelector(`.light-card[data-light-id="${lightId}"]`);
            if (lightCard) {
                if (isOn) {
                    lightCard.classList.add('light-on');
                    lightCard.classList.remove('light-off');
                } else {
                    lightCard.classList.add('light-off');
                    lightCard.classList.remove('light-on');
                }
            }
            
            // APIリクエストを送信
            updateLight(lightId, { on: isOn });
        });
    });
    
    // 明るさスライダーの制御
    const brightnessSliders = document.querySelectorAll('.brightness-slider');
    brightnessSliders.forEach(slider => {
        slider.addEventListener('input', function() {
            // スライダーの値を表示するための処理（オプション）
        });
        
        slider.addEventListener('change', function() {
            const lightId = this.dataset.lightId;
            const brightness = parseInt(this.value);
            
            // APIリクエストを送信
            updateLight(lightId, { brightness: brightness });
        });
    });
    
    // 色相スライダーの制御
    const hueSliders = document.querySelectorAll('.hue-slider');
    hueSliders.forEach(slider => {
        slider.addEventListener('change', function() {
            const lightId = this.dataset.lightId;
            const hue = parseInt(this.value);
            
            // APIリクエストを送信
            updateLight(lightId, { hue: hue });
        });
    });
    
    // 彩度スライダーの制御
    const saturationSliders = document.querySelectorAll('.saturation-slider');
    saturationSliders.forEach(slider => {
        slider.addEventListener('change', function() {
            const lightId = this.dataset.lightId;
            const saturation = parseInt(this.value);
            
            // APIリクエストを送信
            updateLight(lightId, { saturation: saturation });
        });
    });
    
    // すべての照明をオンにするボタン
    const allOnBtn = document.getElementById('all-on-btn');
    if (allOnBtn) {
        allOnBtn.addEventListener('click', function() {
            // すべてのスイッチをオンに設定
            lightSwitches.forEach(switchEl => {
                const lightId = switchEl.dataset.lightId;
                switchEl.checked = true;
                
                // 照明カードのスタイルを更新
                const lightCard = document.querySelector(`.light-card[data-light-id="${lightId}"]`);
                if (lightCard) {
                    lightCard.classList.add('light-on');
                    lightCard.classList.remove('light-off');
                }
                
                // APIリクエストを送信
                updateLight(lightId, { on: true });
            });
        });
    }
    
    // すべての照明をオフにするボタン
    const allOffBtn = document.getElementById('all-off-btn');
    if (allOffBtn) {
        allOffBtn.addEventListener('click', function() {
            // すべてのスイッチをオフに設定
            lightSwitches.forEach(switchEl => {
                const lightId = switchEl.dataset.lightId;
                switchEl.checked = false;
                
                // 照明カードのスタイルを更新
                const lightCard = document.querySelector(`.light-card[data-light-id="${lightId}"]`);
                if (lightCard) {
                    lightCard.classList.add('light-off');
                    lightCard.classList.remove('light-on');
                }
                
                // APIリクエストを送信
                updateLight(lightId, { on: false });
            });
        });
    }
    
    // 更新ボタン
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            location.reload();
        });
    }
    
    // 照明詳細ボタン
    const lightInfoBtns = document.querySelectorAll('.light-info-btn');
    lightInfoBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const lightId = this.dataset.lightId;
            showLightDetails(lightId);
        });
    });
});

/**
 * 照明の状態を更新するAPIを呼び出す関数
 * @param {string} lightId - 照明のID
 * @param {Object} data - 更新するデータ
 */
function updateLight(lightId, data) {
    fetch(`/api/lights/${lightId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('照明の更新に失敗しました');
        }
        return response.json();
    })
    .then(data => {
        console.log('照明を更新しました:', data);
    })
    .catch(error => {
        console.error('エラー:', error);
        alert(`エラーが発生しました: ${error.message}`);
    });
}

/**
 * 照明の詳細情報を表示する関数
 * @param {string} lightId - 照明のID
 */
function showLightDetails(lightId) {
    // 照明の詳細情報を取得
    fetch(`/api/lights`)
    .then(response => {
        if (!response.ok) {
            throw new Error('照明情報の取得に失敗しました');
        }
        return response.json();
    })
    .then(data => {
        const lightInfo = data[lightId];
        if (!lightInfo) {
            throw new Error('照明情報が見つかりません');
        }
        
        // モーダルのタイトルと本文を設定
        const modalTitle = document.getElementById('lightDetailTitle');
        const modalBody = document.getElementById('lightDetailBody');
        
        modalTitle.textContent = `照明詳細: ${lightInfo.name}`;
        
        // 詳細情報のHTMLを生成
        let detailsHtml = `
            <div class="table-responsive">
                <table class="table">
                    <tbody>
                        <tr>
                            <th>名前</th>
                            <td>${lightInfo.name}</td>
                        </tr>
                        <tr>
                            <th>状態</th>
                            <td>${lightInfo.on ? '<span class="badge bg-success">オン</span>' : '<span class="badge bg-danger">オフ</span>'}</td>
                        </tr>
                        <tr>
                            <th>タイプ</th>
                            <td>${lightInfo.type}</td>
                        </tr>
                        <tr>
                            <th>明るさ</th>
                            <td>${lightInfo.brightness} / 254</td>
                        </tr>
                        <tr>
                            <th>接続状態</th>
                            <td>${lightInfo.reachable ? '<span class="badge bg-success">接続可能</span>' : '<span class="badge bg-danger">接続不可</span>'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        
        modalBody.innerHTML = detailsHtml;
        
        // モーダルを表示
        const modal = new bootstrap.Modal(document.getElementById('lightDetailModal'));
        modal.show();
    })
    .catch(error => {
        console.error('エラー:', error);
        alert(`エラーが発生しました: ${error.message}`);
    });
} 