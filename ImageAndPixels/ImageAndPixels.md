# About Image and Color

## Learn About Image

| Topic                                    | Why it matters                                                                |
| ---------------------------------------- | ----------------------------------------------------------------------------- |
| **Pixels**                               | Understand how each pixel contains color info (RGBA, RGB, etc).               |
| **Resolution / DPI**                     | Affects image quality and scaling. Important for printing, OCR, or rendering. |
| **Aspect ratio**                         | Needed for cropping, camera preview, and display without stretching.          |
| **Image formats (JPEG, PNG, WebP, etc)** | Learn what format to use depending on size, transparency, or quality.         |
| **Compression**                          | Helps reduce memory and file size. Learn lossy vs lossless compression.       |
| **Bitmap operations**                    | Learn to crop, resize, rotate, flip, blur, etc., programmatically.            |
| **Color depth**                          | 8-bit vs 16-bit vs 32-bit images; affects quality and file size.              |


## Learn About Color

| Topic                                       | Why it matters                                                                                       |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Color Models**: RGB, ARGB, HSV, YUV, CMYK | Needed for filters, ML vision, or camera frame conversion.                                           |
| **Hex, RGB, and alpha blending**            | Needed to draw overlays, blend images, or apply transparency.                                        |
| **Color filters**                           | To apply effects like grayscale, sepia, night mode, etc.                                             |
| **Brightness / Contrast / Saturation**      | Learn how to modify pixel values correctly.                                                          |
| **Color spaces (sRGB, Adobe RGB, etc)**     | Needed for accurate image reproduction, especially in photography or printing.                       |
| **Color temperature / white balance**       | Critical in camera and image correction.                                                             |
| **YUV ↔ RGB conversion**                    | Very important in real-time camera image processing (especially for Android and iOS camera buffers). |



### Color Models

1. RGB (Red, Green, Blue)

- Definition: RGB is an additive color model used for screens. Colors are made by combining Red, Green, and Blue in varying intensities.
- Range: Usually 0–255 per channel (8-bit), so a pixel is represented as (R, G, B).
- Example:
    - (255, 0, 0) → Red
    - (0, 255, 0) → Green
    - (0, 0, 255) → Blue
    - (255, 255, 255) → White
    - (0, 0, 0) → Black
- Usage: Almost all digital screens, camera previews, image files (PNG, JPEG) use RGB internally.

2. ARGB (Alpha, Red, Green, Blue)

- Definition: ARGB is RGB with transparency. The Alpha channel controls opacity.
- Format: (A, R, G, B) where A = 0–255
    - 0 → fully transparent
    - 255 → fully opaque
- Example:
    - (128, 255, 0, 0) → Semi-transparent red
    - (255, 0, 0, 255) → Opaque blue
- Usage:
    - Drawing overlays, stickers, or UI elements on images or camera preview.
    - Essential for blending images.

3. CMYK (Cyan, Magenta, Yellow, Key/Black)

- Definition: CMYK is a subtractive color model used in printing. Colors are made by subtracting light using ink.
- Components:
    * C = Cyan
    * M = Magenta
    * Y = Yellow
    * K = Black (Key)
- Example:
    * (0, 100, 100, 0) → Red
    * (100, 0, 0, 0) → Cyan
    * (0, 0, 0, 100) → Black
- Usage:
    - Not used in screens; mainly in printing and professional graphic design.
    - Can convert RGB to CMYK when sending images to a printer.


    #### Summary 

    | Model | Channels   | Range  | Type                    | Used for                         |
    | ----- | ---------- | ------ | ----------------------- | -------------------------------- |
    | RGB   | R, G, B    | 0–255  | Additive                | Screens, cameras, digital images |
    | ARGB  | A, R, G, B | 0–255  | Additive + transparency | UI overlays, blending            |
    | CMYK  | C, M, Y, K | 0–100% | Subtractive             | Printing, physical colors        |

    - RGB/ARGB = screens & cameras
    - CMYK = printers
    - Understanding how each channel affects the pixel is key for filters, brightness, contrast, and color correction.