import {
    PoseLandmarker,
    FilesetResolver,
    DrawingUtils
} from "https://cdn.skypack.dev/@mediapipe/tasks-vision@0.10.0";

class PoseDetector {
    constructor() {
        this.poseLandmarker = null;
        this.webcamRunning = false;
        this.lastVideoTime = -1;
        this.webcamStream = null;
        this.runningMode = "IMAGE";
        this.frameCount = 0;
        this.startTime = null;
        this.sendInterval = 1000; // 大幅降低发送频率到1秒
        this.lastSendTime = 0;
        this.animationFrameId = null;
        
        // 后端连接状态
        this.backendAvailable = true;
        this.backendRetryCount = 0;
        this.maxRetryCount = 2;
        
        // 状态显示元素
        this.cameraStatusElement = document.getElementById('cameraStatus');
        this.backendStatusElement = document.getElementById('backendStatus');
        this.frameCountElement = document.getElementById('frameCount');
        
        this.init();
    }

    async init() {
        try {
            this.updateStatus('backendStatus', '初始化中...', 'orange');
            
            const vision = await FilesetResolver.forVisionTasks(
                "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
            );
            
            this.poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`,
                    delegate: "GPU"
                },
                runningMode: this.runningMode,
                numPoses: 1
            });

            this.setupWebcam();
            console.log("PoseLandmarker 初始化完成");
            this.updateStatus('backendStatus', '就绪', 'green');
        } catch (error) {
            console.error("初始化失败:", error);
            this.updateStatus('backendStatus', '初始化失败', 'red');
            alert("模型加载失败，请刷新页面重试");
        }
    }

    setupWebcam() {
        this.video = document.getElementById("webcam");
        this.canvasElement = document.getElementById("output_canvas");
        this.canvasCtx = this.canvasElement.getContext("2d");
        this.drawingUtils = new DrawingUtils(this.canvasCtx);
        
        const enableWebcamButton = document.getElementById("webcamButton");
        enableWebcamButton.addEventListener("click", () => this.enableCam());
        
        if (!this.hasGetUserMedia()) {
            console.warn("getUserMedia() is not supported by your browser");
            enableWebcamButton.disabled = true;
            enableWebcamButton.innerText = "浏览器不支持摄像头";
            this.updateStatus('cameraStatus', '浏览器不支持', 'red');
        }
    }

    hasGetUserMedia() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    async enableCam() {
        if (!this.poseLandmarker) {
            alert("模型尚未加载完成，请稍后重试");
            return;
        }

        if (this.webcamRunning) {
            this.stopWebcam();
        } else {
            await this.startWebcam();
        }
    }

    async startWebcam() {
        this.webcamRunning = true;
        document.getElementById("webcamButton").innerText = "停止摄像头";
        this.frameCount = 0;
        this.startTime = Date.now();
        this.updateStatus('cameraStatus', '启动中...', 'orange');
        
        try {
            // 简化摄像头配置
            const constraints = { 
                video: { 
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 15 } // 降低帧率
                } 
            };
            
            this.webcamStream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.webcamStream;
            
            await new Promise((resolve) => {
                this.video.addEventListener('loadeddata', resolve, { once: true });
            });

            // 切换到视频模式
            if (this.runningMode === "IMAGE") {
                this.runningMode = "VIDEO";
                await this.poseLandmarker.setOptions({ runningMode: "VIDEO" });
            }
            
            this.updateStatus('cameraStatus', '运行中', 'green');
            this.predictWebcam();

        } catch (err) {
            console.error("无法访问摄像头:", err);
            this.updateStatus('cameraStatus', '访问失败', 'red');
            alert("无法访问摄像头，请确保已授予摄像头权限");
            this.webcamRunning = false;
            document.getElementById("webcamButton").innerText = "开启摄像头";
        }
    }

    stopWebcam() {
        this.webcamRunning = false;
        document.getElementById("webcamButton").innerText = "开启摄像头";
        this.updateStatus('cameraStatus', '已停止', 'gray');
        
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }

        if (this.webcamStream) {
            this.webcamStream.getTracks().forEach(track => {
                track.stop();
            });
            this.webcamStream = null;
        }
        
        this.video.srcObject = null;
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
    }

    async predictWebcam() {
        if (!this.webcamRunning || !this.poseLandmarker) {
            return;
        }

        try {
            if (this.video.videoWidth && this.video.videoHeight) {
                this.canvasElement.width = this.video.videoWidth;
                this.canvasElement.height = this.video.videoHeight;
            }

            if (this.lastVideoTime !== this.video.currentTime) {
                this.lastVideoTime = this.video.currentTime;
                const startTimeMs = performance.now();
                
                this.poseLandmarker.detectForVideo(this.video, startTimeMs, (result) => {
                    this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
                    
                    if (result.landmarks) {
                        for (const landmarks of result.landmarks) {
                            this.drawingUtils.drawLandmarks(landmarks, { radius: 3 });
                            this.drawingUtils.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS);
                        }
                    }
                    
                    this.processAndSendResult(result, startTimeMs);
                });
            }
        } catch (error) {
            console.error('预测循环错误:', error);
        }

        if (this.webcamRunning) {
            this.animationFrameId = requestAnimationFrame(() => this.predictWebcam());
        }
    }

    processAndSendResult(result, timestamp) {
        const currentTime = Date.now();
        if (currentTime - this.lastSendTime < this.sendInterval) {
            return;
        }
        this.lastSendTime = currentTime;

        const poseData = this.buildPoseData(result, currentTime);
        this.frameCount++;
        this.frameCountElement.textContent = this.frameCount;

        // 非阻塞发送
        this.sendToBackend(poseData).catch(error => {
            // 静默处理错误，不影响主流程
        });
    }

    buildPoseData(result, currentTime) {
        return {
            left_shoulder: this.getLandmarkData(result.landmarks, 11),
            right_shoulder: this.getLandmarkData(result.landmarks, 12),
            left_elbow: this.getLandmarkData(result.landmarks, 13),
            right_elbow: this.getLandmarkData(result.landmarks, 14),
            left_wrist: this.getLandmarkData(result.landmarks, 15),
            right_wrist: this.getLandmarkData(result.landmarks, 16),
            left_hip: this.getLandmarkData(result.landmarks, 23),
            right_hip: this.getLandmarkData(result.landmarks, 24),
            left_knee: this.getLandmarkData(result.landmarks, 25),
            right_knee: this.getLandmarkData(result.landmarks, 26),
            left_ankle: this.getLandmarkData(result.landmarks, 27),
            right_ankle: this.getLandmarkData(result.landmarks, 28),
            left_heel: this.getLandmarkData(result.landmarks, 29),
            right_heel: this.getLandmarkData(result.landmarks, 30),
            left_foot_index: this.getLandmarkData(result.landmarks, 31),
            right_foot_index: this.getLandmarkData(result.landmarks, 32),
            
            type: "video_frame",
            frame_number: this.frameCount,
            time_seconds: (currentTime - this.startTime) / 1000,
            time_format: this.formatTime((currentTime - this.startTime) / 1000)
        };
    }

    getLandmarkData(landmarks, index) {
        if (landmarks && landmarks[0] && landmarks[0][index]) {
            const landmark = landmarks[0][index];
            return {
                x: parseFloat(landmark.x.toFixed(6)),
                y: parseFloat(landmark.y.toFixed(6)),
                z: parseFloat(landmark.z.toFixed(6)),
                visibility: parseFloat((landmark.visibility || 0).toFixed(6))
            };
        }
        return { x: 0.0, y: 0.0, z: 0.0, visibility: 0.0 };
    }

    formatTime(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    async sendToBackend(poseData) {
        if (!this.backendAvailable) {
            return;
        }

        try {
            // 使用更简单的超时处理
            const response = await fetch('http://localhost:5000/api/pose-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(poseData)
            });

            if (response.ok) {
                this.backendRetryCount = 0;
                this.updateStatus('backendStatus', '连接正常', 'green');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.backendRetryCount++;
            
            if (this.backendRetryCount >= this.maxRetryCount) {
                this.backendAvailable = false;
                this.updateStatus('backendStatus', '连接失败', 'red');
                
                // 60秒后自动重试
                setTimeout(() => {
                    this.backendAvailable = true;
                    this.backendRetryCount = 0;
                    this.updateStatus('backendStatus', '重连中...', 'orange');
                }, 60000);
            }
        }
    }

    updateStatus(elementId, text, color) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
            element.style.color = color;
        }
    }

    destroy() {
        this.stopWebcam();
    }
}

// 初始化检测器
const poseDetector = new PoseDetector();

// 页面关闭时自动停止摄像头
window.addEventListener('beforeunload', () => {
    poseDetector.destroy();
});

// 处理页面可见性变化
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        poseDetector.stopWebcam();
    }
});