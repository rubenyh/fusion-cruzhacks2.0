# Image Upload Feature

This feature allows users to upload images or take photos directly from their mobile device and send them to a backend API.

## Frontend Implementation

### Features
- **Camera Access**: Take photos directly from the camera
- **Gallery Access**: Select images from the device's photo library
- **Image Preview**: Shows selected image before upload
- **Upload Progress**: Loading indicator during upload
- **Error Handling**: User-friendly error messages
- **Permissions**: Automatic permission requests for camera and media library

### API Configuration

The API endpoint is configured via environment variable in `frontend/.env`:

```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
```

The upload endpoint is `/api/upload`.

### Usage
1. Tap "Upload / Take Picture" button
2. Choose between "Take Photo" or "Choose from Gallery"
3. Grant necessary permissions if prompted
4. Preview the selected image
5. Tap "Upload Image" to send to backend
6. Success/error message will be displayed

## Backend Implementation

### FastAPI Server
The backend uses FastAPI with automatic OpenAPI documentation.

### Running the FastAPI Server

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   # Using the startup script
   ./start-server.sh

   # Or manually
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Access points**:
   - API: `http://localhost:8000`
   - Documentation: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/api/health`

### API Requirements

**Endpoint**: `POST /api/upload`

**Content-Type**: `multipart/form-data`

**Form Field**: `image` (file upload)

**Response Format**:
```json
{
  "success": true,
  "message": "Image uploaded successfully",
  "image": {
    "filename": "image-123456789.jpg",
    "originalName": "photo.jpg",
    "size": 1024000,
    "mimetype": "image/jpeg",
    "path": "uploads/image-123456789.jpg",
    "uploadedAt": "2024-01-17T12:00:00.000Z"
  },
  "analysis": {
    // Your AI/ML analysis results here
  }
}
```

### Error Responses
```json
{
  "error": "Error message",
  "details": "Additional error details"
}
```

## Setup Instructions

### Frontend
1. Packages are already installed (`expo-image-picker`, `expo-media-library`)
2. Environment variable is configured in `.env`
3. Update `EXPO_PUBLIC_API_BASE_URL` to match your server IP/port

### Backend
1. Install Python dependencies: `pip install -r requirements.txt`
2. Create `uploads/` directory in backend folder
3. Run the server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Update frontend `.env` with correct server URL

## Security Considerations
- Implement authentication/authorization
- Validate file types and sizes
- Consider rate limiting
- Store uploaded files securely
- Add image processing/validation

## Customization
- Modify image quality/compression in `ImagePicker.launchCameraAsync()` and `launchImageLibraryAsync()`
- Change upload limits in the backend
- Add image resizing/processing
- Implement authentication headers
- Add progress indicators for large uploads