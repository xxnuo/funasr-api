# -*- coding: utf-8 -*-
"""
WebSocket ASR API路由
"""

import logging
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ...services.websocket_asr import get_aliyun_websocket_asr_service

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/ws/v1/asr", tags=["WebSocket ASR"])


@router.websocket("")
async def aliyun_websocket_asr_endpoint(websocket: WebSocket):
    """阿里云WebSocket实时ASR端点"""
    await websocket.accept()
    service = get_aliyun_websocket_asr_service()
    task_id = f"aliyun_ws_asr_{int(time.time())}_{id(websocket)}"

    try:
        await service._process_websocket_connection(websocket, task_id)
    except WebSocketDisconnect:
        logger.info(f"[{task_id}] 客户端断开连接")
    except Exception as e:
        logger.error(f"[{task_id}] 连接处理异常: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get("/test", response_class=HTMLResponse)
async def websocket_asr_test_page():
    """阿里云WebSocket ASR测试页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>阿里云实时语音识别测试</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root {
                --primary-color: #0066cc;
                --primary-hover: #0052a3;
                --danger-color: #d93025;
                --danger-hover: #b31412;
                --bg-color: #f8f9fa;
                --card-bg: #ffffff;
                --text-color: #202124;
                --text-secondary: #5f6368;
                --border-color: #dadce0;
                --shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
            }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background-color: var(--bg-color); color: var(--text-color); line-height: 1.5; }
            .container { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr; gap: 20px; }
            .card { background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow); padding: 24px; border: 1px solid var(--border-color); }
            h1 { margin: 0 0 8px 0; font-size: 22px; font-weight: 500; }
            p.subtitle { margin: 0 0 20px 0; color: var(--text-secondary); font-size: 14px; }
            .grid-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
            .form-group label { display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: var(--text-secondary); }
            input, select { width: 100%; padding: 10px 12px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 14px; box-sizing: border-box; transition: border-color 0.2s; outline: none; }
            input:focus, select:focus { border-color: var(--primary-color); box-shadow: 0 0 0 2px rgba(26,115,232,0.2); }
            .controls { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
            button { padding: 10px 24px; border: none; border-radius: 4px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background-color 0.2s; background-color: #fff; border: 1px solid var(--border-color); color: var(--text-color); }
            button:hover { background-color: #f1f3f4; }
            button.primary { background-color: var(--primary-color); color: white; border: none; }
            button.primary:hover { background-color: var(--primary-hover); }
            button.danger { background-color: var(--danger-color); color: white; border: none; }
            button.danger:hover { background-color: var(--danger-hover); }
            button:disabled { background-color: #f1f3f4; color: #bdc1c6; cursor: not-allowed; border-color: transparent; }
            .status-bar { padding: 12px 16px; border-radius: 4px; background: #e8f0fe; color: #1967d2; font-size: 14px; margin-bottom: 24px; display: flex; align-items: center; }
            .status-bar.error { background: #fce8e6; color: #c5221f; }
            .status-bar.success { background: #e6f4ea; color: #137333; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; margin-bottom: 24px; }
            .stat-item { text-align: center; padding: 16px; background: #f8f9fa; border-radius: 6px; }
            .stat-value { font-size: 20px; font-weight: 600; color: var(--primary-color); margin-bottom: 4px; }
            .stat-label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
            .layout-split { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; height: 500px; }
            .panel { display: flex; flex-direction: column; height: 100%; }
            .panel-header { font-size: 16px; font-weight: 500; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
            .content-area { flex: 1; border: 1px solid var(--border-color); border-radius: 4px; padding: 16px; overflow-y: auto; background: #fff; font-size: 14px; white-space: pre-wrap; word-break: break-all; }
            #log { font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; color: #444; }
            .log-entry { margin-bottom: 4px; border-bottom: 1px solid #f1f3f4; padding-bottom: 4px; }
            .log-time { color: #999; margin-right: 8px; }
            .log-info { color: #1a73e8; }
            .log-success { color: #137333; }
            .log-error { color: #d93025; }
            .log-warning { color: #f9ab00; }
            .intermediate { color: #9aa0a6; }
            @media (max-width: 768px) { .layout-split { grid-template-columns: 1fr; height: auto; } .content-area { height: 300px; } }
            #audioPlaybackContainer { margin-top: 16px; padding: 16px; background: #f8f9fa; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>阿里云实时语音识别</h1>
                <p class="subtitle">WebSocket 实时流式语音识别测试</p>

                <div class="grid-form">
                    <div class="form-group">
                        <label>服务地址</label>
                        <input type="text" id="wsUrl" value="ws://localhost:8000/ws/v1/asr">
                    </div>
                    <div class="form-group">
                        <label>Token (可选)</label>
                        <input type="password" id="token" placeholder="访问令牌">
                    </div>
                    <div class="form-group">
                        <label>音频格式</label>
                        <select id="format"><option value="pcm" selected>PCM (16位)</option></select>
                    </div>
                    <div class="form-group">
                        <label>采样率</label>
                        <select id="sampleRate">
                            <option value="8000">8000 Hz</option>
                            <option value="16000" selected>16000 Hz</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>中间结果</label>
                        <select id="enableIntermediate">
                            <option value="true" selected>开启</option>
                            <option value="false">关闭</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>标点预测</label>
                        <select id="enablePunctuation">
                            <option value="true" selected>开启</option>
                            <option value="false">关闭</option>
                        </select>
                    </div>
                </div>

                <div class="controls">
                    <button id="startBtn" onclick="startRecognition()" class="primary">开始识别</button>
                    <button id="stopBtn" onclick="stopRecognition()" disabled class="danger">停止识别</button>
                    <button onclick="clearLog()">清空日志</button>
                    <button onclick="clearResult()">清空结果</button>
                </div>

                <div id="status" class="status-bar">准备就绪</div>

                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="connectionState">未连接</div>
                        <div class="stat-label">状态</div>
                    </div>
                     <div class="stat-item">
                        <div class="stat-value" id="duration">0.0s</div>
                        <div class="stat-label">时长</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="sentenceCount">0</div>
                        <div class="stat-label">句子</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="audioSize">0 KB</div>
                        <div class="stat-label">数据量</div>
                    </div>
                </div>

                <div id="audioPlaybackContainer" style="display: none;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <h4 style="margin:0">录音回放</h4>
                        <button onclick="downloadAudio()" style="padding: 4px 12px; font-size: 12px;">下载 WAV</button>
                    </div>
                    <audio id="audioPlayback" controls style="width: 100%;"></audio>
                </div>
            </div>

            <div class="layout-split">
                <div class="panel">
                    <div class="panel-header">
                        识别结果
                        <button onclick="copyResult()" style="padding: 4px 12px; font-size: 12px;">复制</button>
                    </div>
                    <div id="resultText" class="content-area"></div>
                </div>
                <div class="panel">
                    <div class="panel-header">系统日志</div>
                    <div id="log" class="content-area"></div>
                </div>
            </div>
        </div>

        <script>
            let websocket = null;
            let taskId = null;
            let mediaRecorder = null;
            let audioContext = null;
            let audioChunksCount = 0;
            let audioSizeTotal = 0;
            let startTime = null;
            let isRecording = false;
            let sentenceCount = 0;
            let sentences = {};
            let recordedAudioChunks = [];
            let recordedBlob = null;
            let sendBuffer = [];

            function generateUUID() {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    const r = Math.random() * 16 | 0;
                    const v = c == 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                }).replace(/-/g, '').substring(0, 32);
            }

            function log(message, type = 'info') {
                const logElement = document.getElementById('log');
                const timestamp = new Date().toLocaleTimeString();
                const entry = document.createElement('div');
                entry.className = `log-entry log-${type}`;
                entry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
                logElement.appendChild(entry);
                logElement.scrollTop = logElement.scrollHeight;
            }

            function updateStatus(message, type = 'info') {
                const statusEl = document.getElementById('status');
                statusEl.textContent = message;
                statusEl.className = `status-bar ${type}`;
            }

            function updateStats() {
                document.getElementById('audioSize').textContent = (audioSizeTotal / 1024).toFixed(1) + ' KB';
                document.getElementById('connectionState').textContent = isRecording ? '录音中' : '未连接';
                document.getElementById('sentenceCount').textContent = sentenceCount;
                if (startTime) {
                    const duration = (Date.now() - startTime) / 1000;
                    document.getElementById('duration').textContent = duration.toFixed(1) + 's';
                }
            }

            function clearLog() {
                document.getElementById('log').innerHTML = '';
                audioChunksCount = 0;
                audioSizeTotal = 0;
                sentenceCount = 0;
                startTime = null;
                updateStats();
            }

            function clearResult() {
                document.getElementById('resultText').textContent = '';
                sentences = {};
            }

            function updateResultDisplay(index, text, isFinal = false) {
                if (!sentences[index]) sentences[index] = { text: "", isFinal: false };
                sentences[index].text = text;
                sentences[index].isFinal = isFinal;

                const resultEl = document.getElementById('resultText');
                let displayHtml = "";
                const indices = Object.keys(sentences).map(Number).sort((a, b) => a - b);

                for (let i = 0; i < indices.length; i++) {
                    const idx = indices[i];
                    const sentence = sentences[idx];
                    if (i > 0) displayHtml += " ";
                    if (sentence.isFinal) {
                        displayHtml += sentence.text;
                    } else {
                        displayHtml += `<span class="intermediate">${sentence.text}</span>`;
                    }
                }
                resultEl.innerHTML = displayHtml;
                resultEl.scrollTop = resultEl.scrollHeight;
            }

            function copyResult() {
                const text = document.getElementById('resultText').innerText;
                if (!text) return;
                navigator.clipboard.writeText(text).then(() => {
                    log('已复制到剪贴板', 'success');
                }).catch(err => {
                    log('复制失败: ' + err, 'error');
                });
            }

            async function startRecognition() {
                const wsUrl = document.getElementById('wsUrl').value;
                if (isRecording) return;

                try {
                    audioChunksCount = 0;
                    audioSizeTotal = 0;
                    sentenceCount = 0;
                    sentences = {};
                    startTime = Date.now();
                    taskId = generateUUID();
                    sendBuffer = [];
                    recordedAudioChunks = [];

                    updateStatus('正在连接...');
                    log(`连接到: ${wsUrl}`);

                    websocket = new WebSocket(wsUrl);
                    websocket.binaryType = 'arraybuffer';

                    websocket.onopen = async () => {
                        updateStats();
                        updateStatus('连接成功，启动设备...', 'success');
                        log('WebSocket 连接成功', 'success');
                        await sendStartTranscription();
                        await startMicrophone();
                    };

                    websocket.onmessage = async (event) => {
                        try {
                            const response = JSON.parse(event.data);
                            await handleMessage(response);
                        } catch (e) {
                            log('消息解析失败: ' + e.message, 'error');
                        }
                    };

                    websocket.onerror = (error) => {
                        log('WebSocket 错误', 'error');
                        updateStatus('连接错误', 'error');
                    };

                    websocket.onclose = () => {
                        isRecording = false;
                        updateStats();
                        updateStatus('连接已关闭');
                        log('连接断开');
                        document.getElementById('startBtn').disabled = false;
                        document.getElementById('stopBtn').disabled = true;
                        if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
                    };

                    document.getElementById('startBtn').disabled = true;

                } catch (e) {
                    updateStatus('启动失败: ' + e.message, 'error');
                }
            }

            async function stopRecognition() {
                if (websocket && taskId) {
                    if (sendBuffer.length > 0) {
                        const totalLen = sendBuffer.reduce((sum, c) => sum + c.length, 0);
                        const merged = new Int16Array(totalLen);
                        let offset = 0;
                        for (const chunk of sendBuffer) {
                            merged.set(chunk, offset);
                            offset += chunk.length;
                        }
                        websocket.send(merged.buffer);
                        sendBuffer = [];
                    }

                    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();

                    const message = {
                        header: {
                            message_id: generateUUID(),
                            task_id: taskId,
                            namespace: 'SpeechTranscriber',
                            name: 'StopTranscription'
                        }
                    };
                    websocket.send(JSON.stringify(message));
                    log('发送停止指令');
                    updateStatus('正在停止...');
                    document.getElementById('stopBtn').disabled = true;
                }
            }

            async function startMicrophone() {
                try {
                    const sampleRate = parseInt(document.getElementById('sampleRate').value);
                    recordedAudioChunks = [];
                    recordedBlob = null;
                    sendBuffer = [];
                    document.getElementById('audioPlaybackContainer').style.display = 'none';

                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                         throw new Error('您的浏览器不支持音频输入，或者页面未在安全上下文(HTTPS/localhost)中运行。');
                    }

                    const stream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            sampleRate: sampleRate,
                            channelCount: 1,
                            echoCancellation: true,
                            noiseSuppression: true
                        }
                    });

                    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: sampleRate });
                    const source = audioContext.createMediaStreamSource(stream);
                    const processor = audioContext.createScriptProcessor(4096, 1, 1);
                    const chunkStride = 9600;

                    processor.onaudioprocess = (event) => {
                        if (websocket && websocket.readyState === WebSocket.OPEN) {
                            const audioData = event.inputBuffer.getChannelData(0);
                            const pcmData = float32To16BitPCM(audioData);

                            recordedAudioChunks.push(new Int16Array(pcmData));
                            sendBuffer.push(new Int16Array(pcmData));

                            const currentBufferLength = sendBuffer.reduce((sum, chunk) => sum + chunk.length, 0);

                            if (currentBufferLength >= chunkStride) {
                                const sendData = new Int16Array(chunkStride);
                                let offset = 0;
                                let remaining = chunkStride;

                                while (remaining > 0 && sendBuffer.length > 0) {
                                    const chunk = sendBuffer[0];
                                    const copyLength = Math.min(remaining, chunk.length);
                                    sendData.set(chunk.subarray(0, copyLength), offset);
                                    offset += copyLength;
                                    remaining -= copyLength;

                                    if (copyLength >= chunk.length) {
                                        sendBuffer.shift();
                                    } else {
                                        sendBuffer[0] = chunk.subarray(copyLength);
                                    }
                                }

                                websocket.send(sendData.buffer);
                                audioChunksCount++;
                                audioSizeTotal += sendData.buffer.byteLength;
                            }
                            updateStats();
                        }
                    };

                    source.connect(processor);
                    processor.connect(audioContext.destination);
                    isRecording = true;
                    document.getElementById('stopBtn').disabled = false;
                    updateStatus('正在识别中', 'success');
                    log('麦克风已启动', 'success');
                } catch (e) {
                    log('麦克风启动失败: ' + e.message, 'error');
                    updateStatus('麦克风错误: ' + e.message, 'error');
                }
            }

            function float32To16BitPCM(float32Array) {
                const buffer = new ArrayBuffer(float32Array.length * 2);
                const view = new DataView(buffer);
                for (let i = 0; i < float32Array.length; i++) {
                    const s = Math.max(-1, Math.min(1, float32Array[i]));
                    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                }
                return new Int16Array(buffer);
            }

            async function handleMessage(response) {
                const header = response.header || {};
                const payload = response.payload || {};
                const name = header.name || '';
                const status = header.status || 0;

                switch (name) {
                    case 'TranscriptionStarted':
                        if (status === 20000000) {
                            updateStatus('识别已开始', 'success');
                        } else {
                            log('开始失败: ' + header.status_message, 'error');
                        }
                        break;
                    case 'SentenceBegin':
                        break;
                    case 'TranscriptionResultChanged':
                        updateResultDisplay(payload.index ?? 1, payload.result || '', false);
                        break;
                    case 'SentenceEnd':
                        sentenceCount++;
                        updateStats();
                        log(`句子结束: ${payload.result}`, 'success');
                        updateResultDisplay(payload.index ?? 1, payload.result || '', true);
                        break;
                    case 'TranscriptionCompleted':
                        updateStatus('识别完成', 'success');
                        log('识别任务完成', 'success');
                        updateStats();
                        saveRecordedAudio();
                        if (websocket) websocket.close();
                        break;
                    case 'TaskFailed':
                        updateStatus('任务失败: ' + header.status_text, 'error');
                        log('任务失败: ' + header.status_text, 'error');
                        if (websocket) websocket.close();
                        break;
                }
            }

            async function sendStartTranscription() {
                const message = {
                    header: {
                        message_id: generateUUID(),
                        task_id: taskId,
                        namespace: 'SpeechTranscriber',
                        name: 'StartTranscription'
                    },
                    payload: {
                        format: document.getElementById('format').value,
                        sample_rate: parseInt(document.getElementById('sampleRate').value),
                        enable_intermediate_result: document.getElementById('enableIntermediate').value === 'true',
                        enable_punctuation_prediction: document.getElementById('enablePunctuation').value === 'true',
                        enable_inverse_text_normalization: true
                    }
                };
                websocket.send(JSON.stringify(message));
                log('发送 StartTranscription');
            }

            function saveRecordedAudio() {
                if (recordedAudioChunks.length === 0) return;
                try {
                    const totalLength = recordedAudioChunks.reduce((acc, chunk) => acc + chunk.length, 0);
                    const mergedData = new Int16Array(totalLength);
                    let offset = 0;
                    for (const chunk of recordedAudioChunks) {
                        mergedData.set(chunk, offset);
                        offset += chunk.length;
                    }
                    const sampleRate = parseInt(document.getElementById('sampleRate').value);
                    recordedBlob = createWavBlob(mergedData, sampleRate);
                    const audioPlayback = document.getElementById('audioPlayback');
                    audioPlayback.src = URL.createObjectURL(recordedBlob);
                    document.getElementById('audioPlaybackContainer').style.display = 'block';
                    log(`录音已保存`, 'success');
                } catch (e) {
                    log('保存录音失败: ' + e.message, 'error');
                }
            }

            function createWavBlob(pcmData, sampleRate) {
                const dataSize = pcmData.length * 2;
                const buffer = new ArrayBuffer(44 + dataSize);
                const view = new DataView(buffer);
                writeString(view, 0, 'RIFF');
                view.setUint32(4, 36 + dataSize, true);
                writeString(view, 8, 'WAVE');
                writeString(view, 12, 'fmt ');
                view.setUint32(16, 16, true);
                view.setUint16(20, 1, true);
                view.setUint16(22, 1, true);
                view.setUint32(24, sampleRate, true);
                view.setUint32(28, sampleRate * 2, true);
                view.setUint16(32, 2, true);
                view.setUint16(34, 16, true);
                writeString(view, 36, 'data');
                view.setUint32(40, dataSize, true);
                for (let i = 0; i < pcmData.length; i++) {
                    view.setInt16(44 + i * 2, pcmData[i], true);
                }
                return new Blob([buffer], { type: 'audio/wav' });
            }

            function writeString(view, offset, string) {
                for (let i = 0; i < string.length; i++) {
                    view.setUint8(offset + i, string.charCodeAt(i));
                }
            }

            function downloadAudio() {
                if (!recordedBlob) return;
                const url = URL.createObjectURL(recordedBlob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `recording_${new Date().getTime()}.wav`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }

            window.onload = function() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/v1/asr`;
                document.getElementById('wsUrl').value = wsUrl;
                updateStats();
            };

            window.onbeforeunload = function() {
                if (websocket) websocket.close();
                if (audioContext) audioContext.close();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
