# Camera2 Vs CameraX 


Let’s say you have a toy camera that can:
- Take pictures 📸
- Show things live on screen like a phone does (preview) 👀
- Look for words using a magnifying glass (like ML Kit) 🔍


## Camera2 (The Complicated Toy)
With Camera2, you have to build the toy camera from parts:

- You need to put together the lens, the screen, the button, and the battery yourself!
- It’s powerful, but very hard to build 
- You have to handle everything — what to show, how fast, when to stop.

Important Camera2 Classes:
- CameraManager –> Like the toy factory manager 🧑‍🏭
- CameraDevice –> The actual camera lens 📷
- CameraCaptureSession –> The group who helps take photos 🎬
- CaptureRequest –> The letter you send saying “Take a photo, please!” 📝
- ImageReader –> The photo album where images are saved 📒

In most cases, we do not need Camera2.
#### When to use CameraX
1. Manual Camera Controls
    - If you need to control:
        - Focus mode (auto, manual, continuous)
        - Exposure (ISO, shutter speed)
        - White balance
        - RAW capture
Example: A professional photography app, barcode scanner requiring precise focus, or a night mode camera.

2. High-Resolution or RAW Images
    - Camera2 allows capturing RAW (DNG) images or very high-resolution images.
    - Useful for apps that process photos in post-processing, like editing apps.

3. Custom Image Processing
    If you need access to camera frames in real-time for:
     - Computer vision
     - Machine learning inference
     - Custom effects
Example: AR apps, ML-based scanner apps, QR code scanning.

4. Video Recording with Advanced Features
    If you need to customize:
     - Frame rate
     - Bitrate
     - Output format
     - Stabilization
Example: Slow-motion video apps or apps needing consistent frame timing.

5. Multi-Camera or Advanced Hardware Use
    Camera2 lets you:
     - Use multiple cameras simultaneously
     - Access logical or physical camera streams
     - Use ultra-wide, telephoto, or depth cameras programmatically
Example: Portrait mode with depth map.

## CameraX (The Easy Toy)

CameraX is like a pre-built toy camera:
- You just add batteries and press a button and it works!
- It uses Camera2 under the hood, but hides all the hard parts.
- You can say “Hey, I want to see the camera,” or “Take a photo,” and it helps you do that easily.


Important CameraX Classes:
- CameraX – The toy camera box 🎁
- Preview – Shows what the camera sees (like your eyes) 👁️
- ImageCapture – Takes a photo 📸
- ImageAnalysis – Looks at what’s on screen and can send it to ML Kit 🔍
- CameraSelector – You choose front or back camera 🔄
- LifecycleCameraController – Makes sure it opens/closes with your app 🕹️


Camera2 is a box of LEGO 🧱 to build your own camera.
CameraX is a ready-to-play LEGO set 🏗️ where you just open, click, and play!


### Big Picture

Imagine you're building a live camera feature in your app. You want to:
1. Show what the camera sees (Preview)
2. Take a photo (ImageCapture)
3. Analyze the image (ImageAnalysis)
To do that, CameraX connects several classes together like this:

[CameraProvider]
      |
      ↓
[Camera] ← CameraSelector
  |   |   \
  |   |    \__ (optional) for front/back
  |   |
  ↓   ↓
[UseCase: Preview] → [PreviewView]  ← shows image on screen
[UseCase: ImageCapture] ← take photos
[UseCase: ImageAnalysis] ← ML Kit or custom image logic

### Class Roles of CameraX Explained


#### 1. ProcessCameraProvider

🧠 Brain of CameraX.It gives you access to the camera hardware. You must use it to bind use cases like Preview, Capture, and Analysis.

```kotlin
val cameraProvider = ProcessCameraProvider.getInstance(context)
```
#### 2. CameraSelector

🎯 Chooses the front or back camera.

```kotlin
CameraSelector.DEFAULT_BACK_CAMERA
```

#### 3. Preview
👀 Live view from the camera.
You connect it to a PreviewView to show it on screen.

```kotlin
val preview = Preview.Builder().build()
preview.setSurfaceProvider(previewView.surfaceProvider)
```

#### 4. ImageCapture
📸 Used to take pictures.

```kotlin
val imageCapture = ImageCapture.Builder().build()
imageCapture.takePicture(...) // snap a photo
```

#### 5. ImageAnalysis
🔍 Used to get frames for analysis (like ML Kit text recognition).
You set an Analyzer that runs on every frame.

```kotlin
val imageAnalyzer = ImageAnalysis.Builder().build()
imageAnalyzer.setAnalyzer(executor, YourAnalyzer())
```
#### 🧷 Connecting Them Together
```kotlin
cameraProvider.bindToLifecycle(
    lifecycleOwner,
    cameraSelector,
    preview,
    imageCapture,
    imageAnalyzer
)
```
