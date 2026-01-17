import React, { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert, Image, ActivityIndicator } from "react-native";
import * as ImagePicker from 'expo-image-picker';

const API_CONFIG = {
  baseUrl: process.env.EXPO_PUBLIC_API_BASE_URL!,
  uploadEndpoint: '/api/upload',
};

export default function UploadScreen() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

const requestPermissions = async () => {
  const camera = await ImagePicker.requestCameraPermissionsAsync();
  const media = await ImagePicker.requestMediaLibraryPermissionsAsync();

  if (camera.status !== 'granted' || media.status !== 'granted') {
    Alert.alert(
      'Permissions Required',
      'Camera and media library permissions are required.',
    );
    return false;
  }

  return true;
};

  const takePhoto = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const pickFromGallery = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const uploadImage = async () => {
    if (!selectedImage) {
      Alert.alert('No Image', 'Please select or take a photo first.');
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      const response = await fetch(selectedImage);
      const blob = await response.blob();

      const fileName = `image_${Date.now()}.jpg`;
      const file = {
        uri: selectedImage,
        name: fileName,
        type: 'image/jpeg',
      };

      formData.append('image', file as any);

      const uploadResponse = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.uploadEndpoint}`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (uploadResponse.ok) {
        const result = await uploadResponse.json();
        Alert.alert('Success', 'Image uploaded successfully!', [
          {
            text: 'OK',
            onPress: () => {
              setSelectedImage(null); 
            }
          }
        ]);
        console.log('Upload result:', result);
      } else {
        throw new Error(`Upload failed: ${uploadResponse.status}`);
      }

    } catch (error) {
      console.error('Upload error:', error);
      Alert.alert('Upload Failed', 'There was an error uploading your image. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const showImageOptions = () => {
    Alert.alert(
      'Select Image Source',
      'Choose how you want to add an image',
      [
        { text: 'Take Photo', onPress: takePhoto },
        { text: 'Choose from Gallery', onPress: pickFromGallery },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>ProductSearch</Text>

      {!selectedImage ? (
        <TouchableOpacity style={styles.uploadButton} onPress={showImageOptions}>
          <Text style={styles.buttonText}>Upload / Take Picture</Text>
        </TouchableOpacity>
      ) : (
        <View style={styles.imageContainer}>
          <Image source={{ uri: selectedImage }} style={styles.selectedImage} />
          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={[styles.actionButton, styles.changeButton]}
              onPress={showImageOptions}
            >
              <Text style={styles.actionButtonText}>Change Image</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.uploadButton]}
              onPress={uploadImage}
              disabled={isUploading}
            >
              {isUploading ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text style={styles.actionButtonText}>Upload Image</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      )}

      <View style={styles.historyContainer}>
        <Text style={styles.historyTitle}>History</Text>

        <View style={styles.historyPlaceholder}>
          <Text style={styles.placeholderText}>
            No history yet...
          </Text>
        </View>

      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
    padding: 20,
    alignItems: "center",
  },

  title: {
    fontSize: 26,
    fontWeight: "bold",
    color: "white",
    marginTop: 60,
    marginBottom: 40,
  },

  uploadButton: {
    backgroundColor: "#2563EB",
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    width: "100%",
    alignItems: "center",
    marginBottom: 30,
  },

  buttonText: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
  },

  historyContainer: {
    width: "100%",
    flex: 1,
  },

  historyTitle: {
    color: "white",
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 10,
  },

  historyPlaceholder: {
    backgroundColor: "#1E293B",
    flex: 1,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },

  placeholderText: {
    color: "#94A3B8",
    fontSize: 16,
  },

  imageContainer: {
    width: "100%",
    alignItems: "center",
    marginBottom: 30,
  },

  selectedImage: {
    width: 300,
    height: 225,
    borderRadius: 12,
    marginBottom: 20,
  },

  buttonRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    width: "100%",
    gap: 10,
  },

  actionButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: "center",
  },

  changeButton: {
    backgroundColor: "#6B7280",
  },

  actionButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
});
