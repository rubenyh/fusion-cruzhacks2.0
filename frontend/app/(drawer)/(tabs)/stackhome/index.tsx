import React, { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Image,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { MaterialCommunityIcons } from "@expo/vector-icons";

const API_CONFIG = {
  baseUrl: process.env.EXPO_PUBLIC_API_BASE_URL!,
  uploadEndpoint: "/api/upload",
};

export default function UploadScreen() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const requestPermissions = async () => {
    const camera = await ImagePicker.requestCameraPermissionsAsync();
    const media = await ImagePicker.requestMediaLibraryPermissionsAsync();

    if (camera.status !== "granted" || media.status !== "granted") {
      Alert.alert(
        "Permissions Required",
        "Camera and media library permissions are required."
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
      Alert.alert("No Image", "Please select or take a photo first.");
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();

      const fileName = `image_${Date.now()}.jpg`;

      const file = {
        uri: selectedImage,
        name: fileName,
        type: "image/jpeg",
      };

      formData.append("file", file as any);

      console.log("Uploading to:", `${API_CONFIG.baseUrl}${API_CONFIG.uploadEndpoint}`);

      const uploadResponse = await fetch(
        `${API_CONFIG.baseUrl}${API_CONFIG.uploadEndpoint}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (uploadResponse.ok) {
        const result = await uploadResponse.json();
        Alert.alert("Success", "Image uploaded successfully!", [
          {
            text: "OK",
            onPress: () => setSelectedImage(null),
          },
        ]);
      } else {
        throw new Error(`Upload failed: ${uploadResponse.status}`);
      }
    } catch (error: any) {
  console.log("UPLOAD ERROR:", error);
  Alert.alert(
    "Upload Failed",
    error.message || String(error)
  );
} finally {
      setIsUploading(false);
    }
  };

  const showImageOptions = () => {
    Alert.alert("Select Image Source", "Choose how you want to add an image", [
      { text: "Take Photo", onPress: takePhoto },
      { text: "Choose from Gallery", onPress: pickFromGallery },
      { text: "Cancel", style: "cancel" },
    ]);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Product Search</Text>

      <View style={styles.card}>
        {!selectedImage ? (
          <TouchableOpacity
            style={styles.mainButton}
            onPress={showImageOptions}
          >
            <MaterialCommunityIcons
              name="camera-plus"
              size={24}
              color="white"
            />
            <Text style={styles.buttonText}>Upload / Take Picture</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.imageContainer}>
            <Image
              source={{ uri: selectedImage }}
              style={styles.selectedImage}
            />

            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.actionButton, styles.changeButton]}
                onPress={showImageOptions}
              >
                <MaterialCommunityIcons
                  name="image-edit"
                  size={20}
                  color="white"
                />
                <Text style={styles.actionButtonText}>Change</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.uploadButton]}
                onPress={uploadImage}
                disabled={isUploading}
              >
                {isUploading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <>
                    <MaterialCommunityIcons
                      name="cloud-upload"
                      size={20}
                      color="white"
                    />
                    <Text style={styles.actionButtonText}>Upload</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>History</Text>

        <View style={styles.historyPlaceholder}>
          <MaterialCommunityIcons
            name="history"
            size={40}
            color="#8f94c1"
          />
          <Text style={styles.placeholderText}>No history yet...</Text>
          <Text style={styles.subText}>
            Uploaded items will appear here
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: "#333552",
    flexGrow: 1,
  },

  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "white",
    marginBottom: 16,
    textAlign: "center",
  },

  card: {
    backgroundColor: "#15193a",
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },

  sectionTitle: {
    color: "white",
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 12,
  },

  mainButton: {
    backgroundColor: "#2563EB",
    paddingVertical: 16,
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },

  buttonText: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
  },

  imageContainer: {
    alignItems: "center",
  },

  selectedImage: {
    width: "100%",
    height: 220,
    borderRadius: 12,
    marginBottom: 16,
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
    borderRadius: 12,
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "center",
    gap: 8,
  },

  changeButton: {
    backgroundColor: "#4b4f75",
  },

  uploadButton: {
    backgroundColor: "#2563EB",
  },

  actionButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },

  historyPlaceholder: {
    backgroundColor: "#1f2247",
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    padding: 30,
  },

  placeholderText: {
    color: "#b3b8e0",
    fontSize: 16,
    marginTop: 10,
  },

  subText: {
    color: "#8f94c1",
    fontSize: 14,
    marginTop: 4,
  },
});
