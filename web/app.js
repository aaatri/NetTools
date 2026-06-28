// NetTools - 前端逻辑

// ─ 页面切换 ──
document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        btn.classList.add('active');
        const pageId = btn.dataset.page;
        document.getElementById(`page-${pageId}`).classList.add('active');
    });
});

// ── 初始化前缀选择器 ──
function initPrefixSelects() {
    const selects = ['subnet-prefix', 'vlsm-prefix'];
    selects.forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            for (let i = 8; i <= 32; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = i;
                if (id === 'subnet-prefix' && i === 24) option.selected = true;
                if (id === 'vlsm-prefix' && i === 22) option.selected = true;
                select.appendChild(option);
            }
        }
    });
}

// ── 工具函数 ──
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(outputId) {
    document.getElementById(outputId).innerHTML = '<p style="color:#999;">执行中...</p>';
}

function showError(outputId, msg) {
    document.getElementById(outputId).innerHTML = `<p class="red">错误：${escapeHtml(msg)}</p>`;
}

// ── 子网计算 ──
async function doSubnetCalc() {
    const network = document.getElementById('subnet-network').value.trim();
    const prefix = parseInt(document.getElementById('subnet-prefix').value);
    const outputId = 'subnet-output';
    
    if (!network) {
        showError(outputId, '请输入网络地址');
        return;
    }
    
    showLoading(outputId);
    try {
        const result = await pywebview.api.subnet_calc(network, prefix);
        if (result.error) {
            showError(outputId, result.error);
            return;
        }
        
        let html = `<h3>子网计算结果</h3><table>`;
        html += `<tr><td class="key">网络地址</td><td><span class="highlight">${escapeHtml(result.network)}</span></td></tr>`;
        html += `<tr><td class="key">网络类别</td><td>Class ${result.class}</td></tr>`;
        html += `<tr><td class="key">CIDR 前缀</td><td>/${result.prefix}</td></tr>`;
        html += `<tr><td class="key">子网掩码</td><td><span class="highlight mono">${escapeHtml(result.mask)}</span></td></tr>`;
        html += `<tr><td class="key">通配符掩码</td><td><span class="highlight mono">${escapeHtml(result.wildcard)}</span></td></tr>`;
        html += `<tr><td class="key">广播地址</td><td><span class="highlight mono">${escapeHtml(result.broadcast)}</span></td></tr>`;
        html += `<tr><td class="key">IP 总数</td><td>${result.total.toLocaleString()}</td></tr>`;
        html += `<tr><td class="key">可用 IP</td><td><strong>${result.usable.toLocaleString()}</strong></td></tr>`;
        html += `<tr><td class="key">首地址</td><td><span class="highlight mono">${escapeHtml(result.first)}</span></td></tr>`;
        html += `<tr><td class="key">末地址</td><td><span class="highlight mono">${escapeHtml(result.last)}</span></td></tr>`;
        html += `</table>`;
        
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── VLSM 划分 ──
async function doVlsm() {
    const network = document.getElementById('vlsm-network').value.trim();
    const prefix = parseInt(document.getElementById('vlsm-prefix').value);
    const hostsStr = document.getElementById('vlsm-hosts').value.trim();
    const outputId = 'vlsm-output';
    
    if (!network || !hostsStr) {
        showError(outputId, '请填写所有字段');
        return;
    }
    
    const hosts = hostsStr.split(',').map(h => parseInt(h.trim())).filter(h => !isNaN(h));
    if (hosts.length === 0) {
        showError(outputId, '主机数格式错误');
        return;
    }
    
    showLoading(outputId);
    try {
        const results = await pywebview.api.vlsm(network, prefix, hosts);
        
        let html = `<h3>VLSM 划分结果</h3><table>`;
        html += `<tr><th>序号</th><th>子网地址</th><th>掩码</th><th>前缀</th><th>主机需求</th><th>可用 IP</th><th>地址范围</th></tr>`;
        
        results.forEach((r, i) => {
            if (r.error) {
                html += `<tr><td>${i+1}</td><td colspan="6" class="red">错误：${escapeHtml(r.subnet || '')}</td></tr>`;
            } else {
                html += `<tr>`;
                html += `<td>${i+1}</td>`;
                html += `<td><span class="highlight mono">${escapeHtml(r.subnet)}</span></td>`;
                html += `<td><span class="highlight mono">${escapeHtml(r.mask)}</span></td>`;
                html += `<td>/${r.prefix}</td>`;
                html += `<td>${r.hosts}</td>`;
                html += `<td>${r.usable}</td>`;
                html += `<td>${escapeHtml(r.first)} - ${escapeHtml(r.last)}</td>`;
                html += `</tr>`;
            }
        });
        
        html += `</table>`;
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── 快速查询 ──
async function doQuery() {
    const target = document.getElementById('query-input').value.trim();
    const outputId = 'query-output';
    
    if (!target) {
        showError(outputId, '请输入 IP 或域名');
        return;
    }
    
    showLoading(outputId);
    try {
        const result = await pywebview.api.quick_query(target);
        
        let html = '';
        if (result.error) {
            html = `<p class="red">无法解析 "${escapeHtml(result.value || '')}": ${escapeHtml(result.error)}</p>`;
        } else if (result.type === 'ip') {
            html = `<h3>IP 解析结果</h3><table>`;
            html += `<tr><td class="key">地址类型</td><td>IPv${result.version} 地址</td></tr>`;
            html += `<tr><td class="key">IP 地址</td><td><span class="highlight mono">${escapeHtml(result.value)}</span></td></tr>`;
            html += `</table>`;
        } else if (result.type === 'domain') {
            html = `<h3>域名解析结果</h3><table>`;
            html += `<tr><td class="key">域名</td><td><span class="highlight">${escapeHtml(result.value)}</span></td></tr>`;
            html += `<tr><td class="key">解析到 (${result.ips.length} 个 IP)</td><td>`;
            result.ips.forEach(ip => {
                html += `<span class="highlight mono">${escapeHtml(ip)}</span><br>`;
            });
            html += `</td></tr></table>`;
        }
        
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── 带宽换算 ──
async function doBwConvert() {
    const value = parseFloat(document.getElementById('bw-value').value);
    const from = document.getElementById('bw-from').value;
    const to = document.getElementById('bw-to').value;
    const outputId = 'bw-output';
    
    if (isNaN(value)) {
        showError(outputId, '请输入有效数字');
        return;
    }
    
    showLoading(outputId);
    try {
        const result = await pywebview.api.bw_convert(value, from, to);
        
        let html = `<h3>带宽换算结果</h3><table>`;
        html += `<tr><td class="key">输入</td><td><span class="highlight mono">${value} ${from}</span></td></tr>`;
        html += `<tr><td class="key">输出</td><td><span class="highlight mono"><strong>${result.toExponential(6)} ${to}</strong></span></td></tr>`;
        html += `</table>`;
        
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── 端口扫描 ──
async function doPortScan() {
    const host = document.getElementById('ps-host').value.trim();
    const portsStr = document.getElementById('ps-ports').value.trim();
    const outputId = 'ps-output';
    
    if (!host || !portsStr) {
        showError(outputId, '请填写所有字段');
        return;
    }
    
    const ports = portsStr.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p));
    if (ports.length === 0) {
        showError(outputId, '端口格式错误');
        return;
    }
    
    showLoading(outputId);
    try {
        const results = await pywebview.api.port_scan(host, ports);
        
        let html = `<h3>端口扫描结果</h3>`;
        html += `<p>共 ${results.length} 个端口，`;
        const openCount = results.filter(r => r.open).length;
        html += `<span class="green">开放 ${openCount}</span>，关闭 ${results.length - openCount}</p>`;
        html += `<table><tr><th>端口</th><th>状态</th><th>服务</th></tr>`;
        
        results.forEach(r => {
            const statusClass = r.open ? 'green' : 'red';
            const statusText = r.open ? '开放' : '关闭';
            html += `<tr>`;
            html += `<td>${r.port}</td>`;
            html += `<td class="${statusClass}">${statusText}</td>`;
            html += `<td>${escapeHtml(r.service)}</td>`;
            html += `</tr>`;
        });
        
        html += `</table>`;
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── IP 归属 ──
async function doWhois() {
    const ip = document.getElementById('whois-ip').value.trim();
    const outputId = 'whois-output';
    
    if (!ip) {
        showError(outputId, '请输入 IP 地址');
        return;
    }
    
    showLoading(outputId);
    try {
        const resultStr = await pywebview.api.whois_ip(ip);
        const data = JSON.parse(resultStr);
        
        if (data.error) {
            showError(outputId, data.error);
            return;
        }
        
        let html = `<h3>IP 归属信息</h3><table>`;
        const fields = [
            ['IP', data.ip],
            ['城市', data.city],
            ['地区', data.region],
            ['国家', data.country],
            ['坐标', data.loc],
            ['运营商', data.org],
            ['邮编', data.postal],
            ['时区', data.timezone]
        ];
        
        fields.forEach(([key, val]) => {
            html += `<tr><td class="key">${key}</td><td><span class="highlight">${escapeHtml(val || 'N/A')}</span></td></tr>`;
        });
        
        html += `</table>`;
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── Ping 检测 ──
async function doPing() {
    const host = document.getElementById('ping-host').value.trim();
    const count = parseInt(document.getElementById('ping-count').value);
    const outputId = 'ping-output';
    
    if (!host) {
        showError(outputId, '请输入主机地址');
        return;
    }
    
    showLoading(outputId);
    try {
        const result = await pywebview.api.ping(host, count);
        
        let html = `<h3>Ping 结果</h3>`;
        html += `<p>成功 <b class="green">${result.successes}/${result.total}</b> 次 (${100 - result.loss_rate}% 成功率)</p>`;
        
        result.results.forEach(r => {
            const dot = r.success ? 'success-dot' : 'fail-dot';
            const status = r.success ? '<span class="pill pill-ok">✓ 成功</span>' : '<span class="pill pill-err">✗ 超时</span>';
            html += `<p><span class="${dot}"></span>第${r.seq} 次：${status}</p>`;
            if (r.success && r.output) {
                html += `<pre>${escapeHtml(r.output)}</pre>`;
            }
        });
        
        html += `<div style="margin-top:12px;">`;
        html += `<span class="pill pill-ok">成功率：${100 - result.loss_rate}%</span>`;
        html += `<span class="pill pill-ok">成功：${result.successes}</span>`;
        if (result.total - result.successes > 0) {
            html += `<span class="pill pill-err">丢失：${result.total - result.successes}</span>`;
        }
        html += `</div>`;
        
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── DNS 查询 ─
async function doDns() {
    const domain = document.getElementById('dns-domain').value.trim();
    const outputId = 'dns-output';
    
    if (!domain) {
        showError(outputId, '请输入域名');
        return;
    }
    
    showLoading(outputId);
    try {
        const results = await pywebview.api.dns_lookup(domain);
        
        let html = `<h3>DNS 解析结果</h3><table>`;
        results.forEach(r => {
            if (r.type === 'error') {
                html += `<tr><td class="key red">错误</td><td class="red">${escapeHtml(r.value)}</td></tr>`;
            } else {
                html += `<tr><td class="key">${r.type} 记录</td><td><span class="highlight mono">${escapeHtml(r.value)}</span></td></tr>`;
            }
        });
        html += `</table>`;
        
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── 路由追踪 ──
async function doTraceroute() {
    const host = document.getElementById('tr-host').value.trim();
    const outputId = 'tr-output';
    
    if (!host) {
        showError(outputId, '请输入目标地址');
        return;
    }
    
    showLoading(outputId);
    try {
        const results = await pywebview.api.traceroute(host);
        
        let html = `<h3>路由追踪结果</h3><table>`;
        results.forEach((r, i) => {
            const isErr = r.raw.toLowerCase().includes('error') || r.raw.toLowerCase().includes('timeout');
            const cls = isErr ? 'red' : '';
            html += `<tr><td style="color:#888;">${i+1}</td><td class="${cls}" style="white-space:pre-wrap;">${escapeHtml(r.raw)}</td></tr>`;
        });
        html += `</table>`;
        
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ─ 进制转换 ──
async function doHexConvert() {
    const value = document.getElementById('hex-value').value.trim();
    const srcBase = document.getElementById('hex-base').value;
    const outputId = 'hex-output';
    
    if (!value) {
        showError(outputId, '请输入数值');
        return;
    }
    
    showLoading(outputId);
    try {
        const result = await pywebview.api.hex_convert(value, srcBase);
        
        if (result.error) {
            showError(outputId, result.error);
            return;
        }
        
        let html = `<h3>转换结果</h3>`;
        html += `<p style="font-size:12px;">源值：<span class="mono">${escapeHtml(result.input)}</span> (基数 ${result.src_base})</p>`;
        html += `<table>`;
        html += `<tr><td class="key">十进制</td><td><span class="mono">${result.dec}</span></td></tr>`;
        html += `<tr><td class="key">十六进制</td><td><span class="highlight mono">${result.hex}</span></td></tr>`;
        html += `<tr><td class="key">八进制</td><td><span class="mono">${result.oct}</span></td></tr>`;
        html += `<tr><td class="key">二进制</td><td><span class="mono">${result.bin}</span></td></tr>`;
        html += `<tr><td class="key">二进制 (4 位分组)</td><td><span class="highlight mono">${result.bin_zfill}</span></td></tr>`;
        html += `</table>`;
        
        document.getElementById(outputId).innerHTML = html;
    } catch (e) {
        showError(outputId, e.message);
    }
}

// ── 思科 MCP ──
var ptDevices = [];
var ptConnections = [];

async function ptConnect() {
    document.getElementById('mcp-connect-text').textContent = '连接中...';
    document.getElementById('mcp-connect-dot').className = 'mcp-dot connecting';
    try {
        // First check if bridge is running via health endpoint
        var healthOk = false;
        try {
            var h = await fetch('http://127.0.0.1:7531/health', { mode: 'no-cors' });
            healthOk = true;
        } catch (_) {
            // fallback: check via API
            var s = await pywebview.api.pt_status();
            healthOk = true;
        }
        const r = await pywebview.api.pt_wait(30);
        if (r.success) {
            document.getElementById('mcp-connect-dot').className = 'mcp-dot connected';
            document.getElementById('mcp-connect-text').textContent = '已连接';
            ptRefreshNetwork();
        } else {
            document.getElementById('mcp-connect-dot').className = 'mcp-dot offline';
            document.getElementById('mcp-connect-text').textContent = '连接失败: ' + r.error;
        }
    } catch (e) {
        document.getElementById('mcp-connect-dot').className = 'mcp-dot offline';
        document.getElementById('mcp-connect-text').textContent = '错误: ' + e.message;
    }
}

async function ptCheckStatus() {
    try {
        const s = await pywebview.api.pt_status();
        if (s.connected) {
            document.getElementById('mcp-connect-dot').className = 'mcp-dot connected';
            document.getElementById('mcp-connect-text').textContent = '已连接';
        } else {
            document.getElementById('mcp-connect-text').textContent = '等待 PT 连接...';
        }
    } catch (_) {
        document.getElementById('mcp-connect-text').textContent = '桥接未就绪';
    }
}

function toArray(obj) {
    if (Array.isArray(obj)) return obj;
    if (obj && typeof obj === 'object') {
        if (typeof obj.length === 'number') {
            var a = [];
            for (var i = 0; i < obj.length; i++) a.push(obj[i]);
            return a;
        }
        var a = [];
        for (var k in obj) {
            if (Object.prototype.hasOwnProperty.call(obj, k) && /^\d+$/.test(k))
                a.push(obj[k]);
        }
        if (a.length) return a;
    }
    return [];
}

async function ptRefreshNetwork() {
    var tableEl = document.getElementById('mcp-topo-table');
    tableEl.innerHTML = '<p style="color:#999;">获取拓扑中...</p>';
    try {
        var net = await pywebview.api.pt_get_network();
        if (net.success === false) {
            tableEl.innerHTML = '<p class="red">获取拓扑失败: ' + escapeHtml(net.error) + '</p>';
            return;
        }
        ptDevices = toArray(net.devices);
        ptConnections = toArray(net.connections);
        document.getElementById('mcp-device-count').textContent = '设备: ' + ptDevices.length;
        document.getElementById('mcp-link-count').textContent = '连接: ' + ptConnections.length;
        if (ptDevices.length === 0) {
            tableEl.innerHTML = '<p class="red">没有设备</p><pre style="font-size:11px;background:#f5f5f5;padding:8px;text-align:left;max-height:200px;overflow:auto;">' + escapeHtml(JSON.stringify(net, null, 2)) + '</pre>';
            return;
        }
        var html = '<table><tr><th>设备名</th><th>型号</th><th>接口数</th></tr>';
        ptDevices.forEach(function(d) {
            var ifaces = toArray(d.interfaces);
            var used = ifaces.filter(function(i) { return i.in_use; }).length;
            html += '<tr><td>' + escapeHtml(d.name) + '</td><td>' + escapeHtml(d.model) + '</td><td>' + ifaces.length + ' (' + used + ' 在用)</td></tr>';
        });
        html += '</table>';
        if (ptConnections.length > 0) {
            html += '<h4 style="margin-top:12px;">连接</h4><table><tr><th>设备1</th><th>接口</th><th>设备2</th><th>接口</th></tr>';
            ptConnections.forEach(function(c) {
                html += '<tr><td>' + escapeHtml(c.from) + '</td><td>' + escapeHtml(c.fromInterface) + '</td><td>' + escapeHtml(c.to) + '</td><td>' + escapeHtml(c.toInterface) + '</td></tr>';
            });
            html += '</table>';
        }
        tableEl.innerHTML = html;
    } catch (e) {
        tableEl.innerHTML = '<p class="red">错误: ' + escapeHtml(e.message) + ' ' + escapeHtml(e.stack) + '</p>';
    }
}

// ── 快速操作 ──
async function ptQuickAddDevice() {
    var name = prompt('设备名称:', 'Router1');
    if (!name) return;
    var model = prompt('设备型号 (2911/1941/2960-24TT/PC-PT/Server-PT):', '2911');
    if (!model) return;
    var x = parseFloat(prompt('X 坐标:', '0')) || 0;
    var y = parseFloat(prompt('Y 坐标:', '0')) || 0;
    try {
        var r = await pywebview.api.pt_add_device(name, model, x, y);
        alert(r.success !== false ? '添加成功' : '失败: ' + (r.error || ''));
        if (r.success !== false) ptRefreshNetwork();
    } catch (e) {
        alert('错误: ' + e.message);
    }
}

async function ptQuickAddLink() {
    var d1 = prompt('设备1 名称:', '');
    if (!d1) return;
    var i1 = prompt('设备1 接口 (如 GigabitEthernet0/0):', '');
    if (!i1) return;
    var d2 = prompt('设备2 名称:', '');
    if (!d2) return;
    var i2 = prompt('设备2 接口:', '');
    if (!i2) return;
    var type = prompt('线缆类型 (straight/cross/fiber/serial/auto):', 'auto') || 'auto';
    try {
        var r = await pywebview.api.pt_add_link(d1, i1, d2, i2, type);
        alert(r.success !== false ? '连接成功' : '失败: ' + (r.error || ''));
        if (r.success !== false) ptRefreshNetwork();
    } catch (e) {
        alert('错误: ' + e.message);
    }
}

async function ptQuickPower() {
    var name = prompt('设备名称:', '');
    if (!name) return;
    var on = confirm('确定要开机吗？\n取消 = 关机');
    try {
        var r = await pywebview.api.pt_set_power(name, on);
        alert(r.success !== false ? (on ? '已开机' : '已关机') : '失败: ' + (r.error || ''));
    } catch (e) {
        alert('错误: ' + e.message);
    }
}

async function ptQuickDelete() {
    var name = prompt('要删除的设备名称:', '');
    if (!name) return;
    if (!confirm('确定删除 ' + name + ' 吗？')) return;
    try {
        var r = await pywebview.api.pt_remove_device([name]);
        alert(r.success !== false ? '已删除' : '失败: ' + (r.error || ''));
        if (r.success !== false) ptRefreshNetwork();
    } catch (e) {
        alert('错误: ' + e.message);
    }
}

// ── 配置模板 ──
var ptTemplates = [];

async function ptLoadTemplates() {
    try {
        var sel = document.getElementById('mcp-template-select');
        sel.innerHTML = '<option value="">-- 选择模板 --</option>';
        ptTemplates = await pywebview.api.pt_get_templates();
        if (!ptTemplates || ptTemplates.length === 0) {
            console.warn('pt_get_templates returned empty');
            return;
        }
        ptTemplates.forEach(function(t) {
            var opt = document.createElement('option');
            opt.value = t.key;
            opt.textContent = (t.name || t.key) + ' - ' + (t.description || '');
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error('ptLoadTemplates error:', e);
    }
}

function ptSelectTemplate() {
    var key = document.getElementById('mcp-template-select').value;
    var fieldsEl = document.getElementById('mcp-template-fields');
    var resultEl = document.getElementById('mcp-template-result');
    resultEl.innerHTML = '';
    if (!key) {
        fieldsEl.innerHTML = '';
        return;
    }

    var t = ptTemplates.find(function(x) { return x.key === key; });
    if (!t) return;

    var html = '';
    t.fields.forEach(function(f) {
        html += '<div class="mcp-field-row">';
        html += '<label>' + escapeHtml(f.label) + '</label>';
        if (f.type === 'select') {
            html += '<select id="mcp-tf-' + f.key + '">';
            (f.options || []).forEach(function(o) {
                var sel = o === (f.default || '') ? ' selected' : '';
                html += '<option value="' + o + '"' + sel + '>' + o + '</option>';
            });
            html += '</select>';
        } else if (f.type === 'checkbox') {
            var chk = f.default ? ' checked' : '';
            html += '<input type="checkbox" id="mcp-tf-' + f.key + '"' + chk + '>';
        } else {
            html += '<input type="' + (f.type === 'number' ? 'number' : 'text') + '" id="mcp-tf-' + f.key + '" value="' + escapeHtml(String(f.default || '')) + '">';
        }
        html += '</div>';
    });
    fieldsEl.innerHTML = html;
}

async function ptGenerateConfig() {
    var key = document.getElementById('mcp-template-select').value;
    var resultEl = document.getElementById('mcp-template-result');
    if (!key) { resultEl.innerHTML = '<p class="red">请选择模板类型</p>'; return; }

    var t = ptTemplates.find(function(x) { return x.key === key; });
    if (!t) return;

    var fields = {};
    t.fields.forEach(function(f) {
        var el = document.getElementById('mcp-tf-' + f.key);
        if (!el) return;
        if (f.type === 'checkbox') fields[f.key] = el.checked;
        else if (f.type === 'number') fields[f.key] = parseFloat(el.value) || 0;
        else fields[f.key] = el.value;
    });

    try {
        var r = await pywebview.api.pt_generate_config(key, fields);
        if (r.success === false) {
            resultEl.innerHTML = '<p class="red">' + escapeHtml(r.error) + '</p>';
            return;
        }
        var html = '<h4>生成的 IOS 配置:</h4><pre class="mcp-config-block">';
        (r.commands || []).forEach(function(cmd) {
            html += escapeHtml(cmd) + '\n';
        });
        html += '</pre>';
        resultEl.innerHTML = html;
        resultEl.dataset.commands = JSON.stringify(r.commands);
    } catch (e) {
        resultEl.innerHTML = '<p class="red">错误: ' + escapeHtml(e.message) + '</p>';
    }
}

// ── AI 配置 ──
async function ptAiLoadConfig() {
    try {
        var cfg = await pywebview.api.pt_ai_load_config();
        document.getElementById('ai-api-endpoint').value = cfg.endpoint || '';
        document.getElementById('ai-api-key').value = cfg.key || '';
        document.getElementById('ai-api-model').value = cfg.model || 'gpt-4o';
    } catch (e) {}
}

function ptAiShowSettings() {
    ptAiLoadConfig();
    document.getElementById('ai-settings-overlay').style.display = 'flex';
}

function ptAiCloseSettings() {
    document.getElementById('ai-settings-overlay').style.display = 'none';
}

async function ptAiSaveSettings() {
    var data = {
        endpoint: document.getElementById('ai-api-endpoint').value.trim(),
        key: document.getElementById('ai-api-key').value.trim(),
        model: document.getElementById('ai-api-model').value.trim() || 'gpt-4o',
    };
    try {
        var r = await pywebview.api.pt_ai_save_config(data);
        var el = document.getElementById('ai-settings-status');
        if (r.success) {
            el.textContent = '✓ 已保存';
        } else {
            el.textContent = '✗ ' + (r.error || '保存失败');
        }
        setTimeout(function() { el.textContent = ''; }, 3000);
    } catch (e) {
        alert('保存失败: ' + e.message);
    }
}

function ptAiOpenLog() {
    var overlay = document.getElementById('ai-log-overlay');
    document.getElementById('ai-log-content').innerHTML = '';
    overlay.style.display = 'flex';
}

function ptAiCloseLog() {
    document.getElementById('ai-log-overlay').style.display = 'none';
}

function ptAiLog(text, cls) {
    var content = document.getElementById('ai-log-content');
    content.innerHTML += '<div class="log-line log-' + (cls || 'info') + '">' + escapeHtml(text) + '</div>';
    content.scrollTop = content.scrollHeight;
}

async function ptAiAutoConfig() {
    var req = document.getElementById('ai-req').value.trim();
    if (!req) { alert('请输入需求描述'); return; }

    ptAiOpenLog();
    ptAiLog('=== AI 自动配置 ===', 'info');
    ptAiLog('', 'info');

    ptAiLog('读取拓扑...', 'wait');
    var net;
    try {
        net = await pywebview.api.pt_get_network();
        if (net.success === false) {
            ptAiLog('读取拓扑失败: ' + (net.error || ''), 'err');
            return;
        }
    } catch (e) {
        ptAiLog('读取拓扑异常: ' + e.message, 'err');
        return;
    }

    var devs = toArray(net.devices);
    var conns = toArray(net.connections);
    ptAiLog('拓扑: ' + devs.length + ' 台设备, ' + conns.length + ' 条连接', 'ok');
    ptAiLog('', 'info');

    ptAiLog('AI 生成配置中（可能需要几秒）...', 'wait');
    var result;
    try {
        result = await pywebview.api.pt_ai_generate_config(req);
    } catch (e) {
        ptAiLog('AI 请求异常: ' + e.message, 'err');
        return;
    }

    if (result.error) {
        ptAiLog('错误: ' + result.error, 'err');
        return;
    }

    if (result.warnings && result.warnings.length) {
        result.warnings.forEach(function(w) { ptAiLog('⚠ ' + w, 'wait'); });
        ptAiLog('', 'info');
    }
    if (result.errors && result.errors.length) {
        result.errors.forEach(function(e) { ptAiLog('✗ ' + e, 'err'); });
        ptAiLog('', 'info');
    }

    var configs = result.configs || [];
    if (configs.length === 0) {
        ptAiLog('AI 未生成任何配置', 'err');
        return;
    }

    ptAiLog('━━━━━━ 推荐配置（共 ' + configs.length + ' 台）━━━━━━', 'info');
    ptAiLog(result.configText || '(空)', 'cmd');
    ptAiLog('', 'info');
    ptAiLog('━━━━━━ 完成 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'info');
}

// ── 自然语言 → IOS 配置 ──
async function ptParseNl() {
    var text = document.getElementById('mcp-nl-input').value.trim();
    var resultEl = document.getElementById('mcp-nl-result');
    if (!text) { resultEl.innerHTML = '<p class="red">请输入需求描述</p>'; return; }

    resultEl.innerHTML = '<p style="color:#999;">AI 生成中...</p>';
    try {
        var r = await pywebview.api.pt_parse_nl(text);
        if (!r.matched) {
            resultEl.innerHTML = '<p class="red">' + escapeHtml(r.error) + '</p>';
            return;
        }

        var cmds = r.commands || [];
        var html = '<pre class="mcp-config-block">';
        cmds.forEach(function(cmd) {
            html += escapeHtml(cmd) + '\n';
        });
        html += '</pre>';
        resultEl.innerHTML = html;
    } catch (e) {
        resultEl.innerHTML = '<p class="red">错误: ' + escapeHtml(e.message) + '</p>';
    }
}

// ── 页面切换时检查 MCP 状态 ──
document.querySelectorAll('.nav-item').forEach(function(btn) {
    btn.addEventListener('click', function() {
        if (btn.dataset.page === 'ciscomcp') {
            setTimeout(ptCheckStatus, 100);
            setTimeout(ptLoadTemplates, 200);
            setTimeout(ptAiLoadConfig, 300);
        }
    });
});

// ── 加载应用图标（侧边栏 + 关于页面） ──
async function ptLoadAppIcon() {
    try {
        var dataUrl = await pywebview.api.pt_get_app_icon();
        if (dataUrl) {
            var sidebar = document.getElementById('logo-icon-img');
            if (sidebar) { sidebar.src = dataUrl; }
            var about = document.getElementById('about-icon-img');
            if (about) { about.src = dataUrl; about.style.display = ''; }
        }
    } catch (e) {}
}

// ── 初始化 ──
window.addEventListener('DOMContentLoaded', () => {
    initPrefixSelects();
});
window.addEventListener('pywebviewready', () => {
    ptLoadAppIcon();
});
