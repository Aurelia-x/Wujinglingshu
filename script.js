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
        this.webcamStream = null; // 新增：保存摄像头流引用
        this.runningMode = "IMAGE"; // 初始模式
        this.init();
    }

    async init() {
        try {
            // 初始化MediaPipe
            const vision = await FilesetResolver.forVisionTasks(
                "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
            );
            
            this.poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`,
                    delegate: "GPU"
                },
                runningMode: this.runningMode,
                numPoses: 2 // 可以检测多个人
            });

            this.setupWebcam();
            console.log("PoseLandmarker 初始化完成");
        } catch (error) {
            console.error("初始化失败:", error);
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
        
        // 检查浏览器支持
        if (!this.hasGetUserMedia()) {
            console.warn("getUserMedia() is not supported by your browser");
            enableWebcamButton.disabled = true;
            enableWebcamButton.innerText = "浏览器不支持摄像头";
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
            // 停止摄像头和检测
            this.stopWebcam();
        } else {
            // 开启摄像头和检测
            await this.startWebcam();
        }
    }

    async startWebcam() {
        this.webcamRunning = true;
        document.getElementById("webcamButton").innerText = "停止摄像头";
        
        try {
            // 获取摄像头权限
            const constraints = { 
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            };
            
            this.webcamStream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.webcamStream;
            
            // 切换到视频模式
            if (this.runningMode === "IMAGE") {
                this.runningMode = "VIDEO";
                await this.poseLandmarker.setOptions({ runningMode: "VIDEO" });
            }
            
            this.video.addEventListener("loadeddata", () => this.predictWebcam());
            
        } catch (err) {
            console.error("无法访问摄像头:", err);
            alert("无法访问摄像头，请确保已授予摄像头权限");
            this.webcamRunning = false;
            document.getElementById("webcamButton").innerText = "开启摄像头";
        }
    }

    stopWebcam() {
        this.webcamRunning = false;
        document.getElementById("webcamButton").innerText = "开启摄像头";
        
        // 停止所有视频轨道
        if (this.webcamStream) {
            this.webcamStream.getTracks().forEach(track => {
                track.stop();
            });
            this.webcamStream = null;
        }
        
        // 清空视频源
        this.video.srcObject = null;
        
        // 清空画布
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
    }

    async predictWebcam() {
        // 安全检查
        if (!this.webcamRunning || !this.poseLandmarker) {
            return;
        }

        // 设置canvas尺寸与视频一致
        if (this.video.videoWidth && this.video.videoHeight) {
            this.canvasElement.width = this.video.videoWidth;
            this.canvasElement.height = this.video.videoHeight;
        }

        // 只在视频帧更新时检测
        if (this.lastVideoTime !== this.video.currentTime) {
            this.lastVideoTime = this.video.currentTime;
            const startTimeMs = performance.now();
            
            // 使用回调函数方式检测姿势（官方推荐）
            this.poseLandmarker.detectForVideo(this.video, startTimeMs, (result) => {
                // 清空画布
                this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
                
                // 绘制检测结果
                if (result.landmarks) {
                    for (const landmarks of result.landmarks) {
                        // 绘制关键点
                        this.drawingUtils.drawLandmarks(landmarks, {
                            radius: (data) => DrawingUtils.lerp(data.from.z, -0.15, 0.1, 5, 1)
                        });
                        // 绘制连接线
                        this.drawingUtils.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS);
                    }
                }
            });
        }

        // 持续检测
        if (this.webcamRunning) {
            requestAnimationFrame(() => this.predictWebcam());
        }
    }

    // 页面关闭时自动清理
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