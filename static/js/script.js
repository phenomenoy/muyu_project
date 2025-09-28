/**
 * 木鱼点击计数器 - 前端逻辑
 * 功能：
 * - 木鱼点击事件处理
 * - 点击动画特效
 * - AJAX 请求更新计数
 * - 状态检查功能
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🪵 木鱼计数器前端加载完成');
    
    // DOM 元素
    const muyuImage = document.getElementById('muyu');
    const clickCount = document.getElementById('click-count');
    const clickEffect = document.getElementById('click-effect');
    const healthBtn = document.getElementById('health-btn');
    const statusMessage = document.getElementById('status-message');
    
    let clickCounter = 0; // 本地计数备份
    let isProcessing = false; // 防止重复点击
    
    // ========================================
    // 木鱼点击事件
    // ========================================
    muyuImage.addEventListener('click', handleMuyuClick);
    
    function handleMuyuClick(event) {
        // 防止重复点击
        if (isProcessing) return;
        isProcessing = true;
        
        console.log('🪵 木鱼被点击');
        clickCounter++;
        
        // 触发点击特效
        triggerClickEffect(event);
        
        // 添加点击动画类
        muyuImage.classList.add('clicked');
        
        // 发送 AJAX 请求
        updateClickCount()
            .then(newCount => {
                // 更新显示
                clickCount.textContent = newCount;
                clickCount.style.color = '#ff6b6b';
                
                // 计数数字动画
                setTimeout(() => {
                    clickCount.style.color = '#fff';
                }, 200);
                
                console.log(`✅ 点击计数更新: ${newCount} 次`);
            })
            .catch(error => {
                console.error('❌ 更新计数失败:', error);
                showStatus('⚠️ 网络错误，请重试', 'error');
            })
            .finally(() => {
                // 移除动画类
                setTimeout(() => {
                    muyuImage.classList.remove('clicked');
                    isProcessing = false;
                }, 300);
            });
    }
    
    // ========================================
    // 更新计数 AJAX 请求
    // ========================================
    function updateClickCount() {
        return fetch('/click', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                timestamp: Date.now(),
                client_count: clickCounter
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                return data.clicks;
            } else {
                throw new Error(data.message || '服务器错误');
            }
        });
    }
    
    // ========================================
    // 点击特效
    // ========================================
    function triggerClickEffect(event) {
        // 创建粒子效果
        const particle = clickEffect.cloneNode(true);
        particle.style.left = event.offsetX + 'px';
        particle.style.top = event.offsetY + 'px';
        particle.classList.add('active');
        
        document.querySelector('.muyu-container').appendChild(particle);
        
        // 移除粒子
        setTimeout(() => {
            particle.remove();
        }, 600);
        
        // 播放点击音效（可选）
        // playClickSound();
    }
    
    // ========================================
    // 状态检查
    // ========================================
    healthBtn.addEventListener('click', checkHealth);
    
    function checkHealth() {
        console.log('🔍 检查系统状态...');
        healthBtn.textContent = '检查中...';
        healthBtn.disabled = true;
        
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                const status = data.status === 'healthy' && data.database === 'OK' 
                    ? 'success' : 'error';
                const message = data.status === 'healthy' 
                    ? `✅ 系统正常，数据库连接成功` 
                    : `❌ 系统异常: ${data.database}`;
                
                showStatus(message, status);
                console.log('📊 健康检查结果:', data);
            })
            .catch(error => {
                showStatus('❌ 无法连接服务器', 'error');
                console.error('健康检查失败:', error);
            })
            .finally(() => {
                healthBtn.textContent = '检查状态';
                healthBtn.disabled = false;
            });
    }
    
    // ========================================
    // 状态消息显示
    // ========================================
    function showStatus(message, type = 'info') {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        
        // 自动隐藏
        setTimeout(() => {
            statusMessage.textContent = '';
            statusMessage.className = 'status-message';
        }, 3000);
    }
    
    // ========================================
    // 页面加载完成
    // ========================================
    // 初始状态检查
    setTimeout(checkHealth, 1000);
    
    // 键盘快捷键：空格键点击木鱼
    document.addEventListener('keydown', function(event) {
        if (event.code === 'Space') {
            event.preventDefault();
            muyuImage.click();
        }
    });
    
    console.log('🎯 木鱼计数器已就绪！点击木鱼开始禅修~');
});