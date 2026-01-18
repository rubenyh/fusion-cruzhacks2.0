import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from "react-native";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useLocalSearchParams } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";

const API_CONFIG = {
  baseUrl: process.env.EXPO_PUBLIC_API_BASE_URL!,
};

export default function ResultsScreen() {
  const params = useLocalSearchParams();
  const report = params.report ? JSON.parse(params.report as string) : null;

  const [isDownloading, setIsDownloading] = useState(false);

  if (!report) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>No Report Data</Text>
      </View>
    );
  }

const downloadPdf = async () => {
  try {
    setIsDownloading(true);

    const res = await fetch(`${API_CONFIG.baseUrl}/report-pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ report }),
    });

    if (!res.ok) throw new Error("Failed to generate PDF");

    const blob = await res.blob();

    const fileUri = FileSystem.cacheDirectory + "report.pdf";

    const reader = new FileReader();

    reader.onload = async () => {
      const base64data = (reader.result as string).split(",")[1];

      await FileSystem.writeAsStringAsync(fileUri, base64data, {
        encoding: FileSystem.EncodingType.Base64,
      });

      await Sharing.shareAsync(fileUri);
    };

    reader.readAsDataURL(blob);

  } catch (err: any) {
    Alert.alert("Error", err.message || "Could not download PDF");
  } finally {
    setIsDownloading(false);
  }
};


const renderSection = (title: string, content: any, key: string) => (
  <View style={styles.card} key={key}>
    <Text style={styles.sectionTitle}>{title}</Text>
    <Text style={styles.contentText}>
      {typeof content === "string"
        ? content
        : JSON.stringify(content, null, 2)}
    </Text>
  </View>
);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Product Report</Text>

      {Object.entries(report).map(([key, value]) =>
        renderSection(key, value, key)
      )}
      <TouchableOpacity
        style={styles.pdfButton}
        onPress={downloadPdf}
        disabled={isDownloading}
      >
        {isDownloading ? (
          <ActivityIndicator color="white" />
        ) : (
          <>
            <MaterialCommunityIcons name="file-pdf-box" size={22} color="white" />
            <Text style={styles.pdfButtonText}>Download PDF</Text>
          </>
        )}
      </TouchableOpacity>
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
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 8,
  },
  contentText: {
    color: "#b3b8e0",
    fontSize: 14,
  },
  pdfButton: {
    backgroundColor: "#2563EB",
    paddingVertical: 16,
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    marginBottom: 40,
  },
  pdfButtonText: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
  },
});
