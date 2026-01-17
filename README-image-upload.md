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

The API endpoint is easily configurable in `frontend/app/(drawer)/(tabs)/stackhome/index.tsx`:

```javascript
const API_CONFIG = {
  baseUrl: 'http://localhost:3000', // Change this to your backend URL
  uploadEndpoint: '/api/upload', // Change this to your upload endpoint
};
```

### Usage
1. Tap "Upload / Take Picture" button
2. Choose between "Take Photo" or "Choose from Gallery"
3. Grant necessary permissions if prompted
4. Preview the selected image
5. Tap "Upload Image" to send to backend
6. Success/error message will be displayed

## Backend Implementation

### Example Server
See `backend/example-server.js` for a complete Node.js/Express implementation.

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
2. Permissions are handled automatically
3. Update `API_CONFIG` with your backend URL

### Backend
1. Install dependencies: `npm install express multer`
2. Create `uploads/` directory
3. Run the server: `node example-server.js`
4. Update frontend `API_CONFIG.baseUrl` to match your server

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