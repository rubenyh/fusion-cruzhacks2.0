import React, { useState, useEffect } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert, Image, ActivityIndicator, ScrollView } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useAuth } from "@/context/AuthContext";
import { fetchWithAuthToken } from "@/utils/fetchWithAuthToken";
import { useRouter } from "expo-router";
import TaskProgressModal from "@/components/ui/TaskProgressModal";

const API_CONFIG = { 
  baseUrl: process.env.EXPO_PUBLIC_API_BASE_URL!, 
  uploadEndpoint: "/report-json",
  historyEndpoint: "/reports"
};

  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [pendingRequestId, setPendingRequestId] = useState<string | null>(null);
  const { isAuthenticated, login, getCredentials } = useAuth();
  const router = useRouter();

  const requestPermissions = async () => {
    const camera = await ImagePicker.requestCameraPermissionsAsync();
    const media = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (camera.status !== "granted" || media.status !== "granted") {
      Alert.alert("Permissions Required", "Camera and media library permissions are required.");
      return false;
    }
    return true;
  };

  const takePhoto = async () => {
    if (!(await requestPermissions())) return;
    const result = await ImagePicker.launchCameraAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, allowsEditing: true, aspect: [4,3], quality: 0.8 });
    if (!result.canceled && result.assets[0]) setSelectedImage(result.assets[0].uri);
  };

  const pickFromGallery = async () => {
    if (!(await requestPermissions())) return;
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, allowsEditing: true, aspect: [4,3], quality: 0.8 });
    if (!result.canceled && result.assets[0]) setSelectedImage(result.assets[0].uri);
  };

const uploadImage = async () => {
  if (!selectedImage) {
    Alert.alert("No Image", "Please select or take a photo first.");
    return;
  }

  setIsUploading(true);

  try {
    const token = await (typeof getCredentials === 'function' ? getCredentials() : null);
    if (!token) {
      Alert.alert("Not Authenticated", "Please log in first.");
      setIsUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append("image", {
      uri: selectedImage,
      name: "photo.jpg",
      type: "image/jpeg",
    } as any);

    const res = await fetch(
      `${API_CONFIG.baseUrl}${API_CONFIG.uploadEndpoint}`,
      {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      }
    );

    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);

    const json = await res.json();
    setPendingRequestId(json.request_id);
    setShowTaskModal(true);
    setSelectedImage(null);
    fetchHistory();
  } catch (err: any) {
    Alert.alert("Upload Failed", err.message || String(err));
  } finally {
    setIsUploading(false);
  }
};

const fetchHistory = async () => {
  if (!isAuthenticated) return;

  setLoadingHistory(true);

  try {
    const token = await (typeof getCredentials === 'function' ? getCredentials() : null);
    if (!token) {
      setHistory([]);
      setLoadingHistory(false);
      return;
    }
    const data = await fetchWithAuthToken(
      `${API_CONFIG.baseUrl}${API_CONFIG.historyEndpoint}`,
      token
    );

    console.log("Fetched history:", data);

    // Backend returns an array directly now
    const reports = Array.isArray(data) ? data : [];

    setHistory(
      reports.sort(
        (a: any, b: any) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime()
      )
    );
  } catch (err) {
    console.error(err);
    setHistory([]);
  } finally {
    setLoadingHistory(false);
  }
};

  useEffect(() => { fetchHistory(); }, [isAuthenticated]);

  return (
    <>
      <TaskProgressModal
        visible={showTaskModal}
        onClose={() => setShowTaskModal(false)}
        requestId={pendingRequestId || ''}
        apiBaseUrl={API_CONFIG.baseUrl}
        onComplete={report => {
          setShowTaskModal(false);
          setPendingRequestId(null);
          router.push({
            pathname: "/(drawer)/(tabs)/stackhome/results",
            params: {
              report: JSON.stringify({
                ...report.final_report,
                request_id: report.request_id,
                image_url: report.image_url,
              }),
            },
          });
        }}
      />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Product Search</Text>

        <View style={styles.card}>
          {!selectedImage ? (
            <TouchableOpacity style={styles.mainButton} onPress={() => Alert.alert("Select Image Source", "", [
              { text: "Take Photo", onPress: takePhoto },
              { text: "Choose from Gallery", onPress: pickFromGallery },
              { text: "Cancel", style: "cancel" },
            ])}>
              <MaterialCommunityIcons name="camera-plus" size={24} color="white"/>
              <Text style={styles.buttonText}>Upload / Take Picture</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.imageContainer}>
              <Image source={{ uri: selectedImage }} style={styles.selectedImage} />
              <View style={styles.buttonRow}>
                <TouchableOpacity style={[styles.actionButton, styles.changeButton]} onPress={() => setSelectedImage(null)}>
                  <MaterialCommunityIcons name="image-edit" size={20} color="white"/>
                  <Text style={styles.actionButtonText}>Change</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.actionButton, styles.uploadButton]} onPress={uploadImage} disabled={isUploading}>
                  {isUploading ? <ActivityIndicator color="white"/> : <>
                    <MaterialCommunityIcons name="cloud-upload" size={20} color="white"/>
                    <Text style={styles.actionButtonText}>Upload</Text>
                  </>}
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>


        <View style={styles.card}>
          <Text style={styles.sectionTitle}>History</Text>
          {isAuthenticated ? (
            <>
              <TouchableOpacity style={[styles.mainButton, { marginBottom: 12 }]} onPress={fetchHistory}>
                <MaterialCommunityIcons name="refresh" size={20} color="white"/>
                <Text style={styles.buttonText}>Refresh History</Text>
              </TouchableOpacity>
              {loadingHistory ? (
                <ActivityIndicator color="white" size="large" />
              ) : history.length === 0 ? (
                <Text style={styles.placeholderText}>No history yet...</Text>
              ) : (
                history.map((item: any) => (
                  <TouchableOpacity
                    key={item.request_id}
                    style={styles.historyItem}
                    onPress={() =>
                      router.push({
                        pathname: "/(drawer)/(tabs)/stackhome/results",
                        params: {
                          report: JSON.stringify({
                            ...item.final_report,
                            request_id: item.request_id,
                            image_url: item.image_url,
                          }),
                        },
                      })
                    }
                  >
                    <View style={styles.historyHeader}>
                      <MaterialCommunityIcons name="file-document" size={20} color="#b3b8e0" />
                      <Text style={styles.historyTitle}>
                        {item.final_report?.title || "Product Report"}
                      </Text>
                    </View>
                    <Text style={styles.historySubtext}>
                      {item.detection?.product?.product_name || "Unknown Product"}
                    </Text>
                    <Text style={styles.historyMeta}>
                      Risk Level: {item.final_report?.executive_summary?.overall_risk_level || "N/A"}
                    </Text>
                    <Text style={styles.historyDate}>
                      {new Date(item.created_at).toLocaleString()}
                    </Text>
                  </TouchableOpacity>
                ))
              )}
            </>
          ) : (
            <View style={styles.historyPlaceholder}>
              <Text style={styles.placeholderText}>Login to save history!</Text>
              <TouchableOpacity style={styles.loginButton} onPress={login}>
                <Text style={styles.loginButtonText}>Log In</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: "#333552", flexGrow: 1 },
  title: { fontSize: 24, fontWeight: "bold", color: "white", marginBottom: 16, textAlign: "center" },
  card: { backgroundColor: "#15193a", borderRadius: 16, padding: 16, marginBottom: 16 },
  sectionTitle: { color: "white", fontSize: 20, fontWeight: "bold", marginBottom: 12 },
  mainButton: { backgroundColor: "#2563EB", paddingVertical: 16, borderRadius: 12, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10 },
  buttonText: { color: "white", fontSize: 18, fontWeight: "600" },
  imageContainer: { alignItems: "center" },
  selectedImage: { width: "100%", height: 220, borderRadius: 12, marginBottom: 16 },
  buttonRow: { flexDirection: "row", justifyContent: "space-between", width: "100%", gap: 10 },
  actionButton: { flex: 1, paddingVertical: 14, borderRadius: 12, alignItems: "center", flexDirection: "row", justifyContent: "center", gap: 8 },
  changeButton: { backgroundColor: "#4b4f75" },
  uploadButton: { backgroundColor: "#2563EB" },
  actionButtonText: { color: "white", fontSize: 16, fontWeight: "600" },
  historyPlaceholder: { backgroundColor: "#1f2247", borderRadius: 12, justifyContent: "center", alignItems: "center", padding: 30 },
  placeholderText: { color: "#b3b8e0", fontSize: 16, marginTop: 10 },
  loginButton: { backgroundColor: "#2563EB", paddingVertical: 10, paddingHorizontal: 20, borderRadius: 8, marginTop: 12 },
  loginButtonText: { color: "white", fontSize: 16, fontWeight: "600" },
historyItem: {
  backgroundColor: "#1f2247",
  borderRadius: 14,
  padding: 14,
  marginBottom: 12,
  borderWidth: 1,
  borderColor: "#2f3260",
},

historyHeader: {
  flexDirection: "row",
  alignItems: "center",
  gap: 8,
},

historyTitle: {
  color: "white",
  fontSize: 16,
  fontWeight: "bold",
},

historySubtext: {
  color: "#b3b8e0",
  marginTop: 6,
  fontSize: 14,
},

historyMeta: {
  color: "#8f94c2",
  marginTop: 6,
  fontSize: 13,
},

historyDate: {
  color: "#666b99",
  marginTop: 6,
  fontSize: 12,
},
});
