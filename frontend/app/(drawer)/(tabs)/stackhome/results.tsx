import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Image,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useAuth } from "@/context/AuthContext";

const API_CONFIG = {
  baseUrl: process.env.EXPO_PUBLIC_API_BASE_URL!,
};

export default function ResultsScreen() {
  const params = useLocalSearchParams();
  const { getCredentials  } = useAuth();

  const report = params.report ? JSON.parse(params.report as string) : null;

  const [isDownloading, setIsDownloading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const deleteReport = async () => {
    Alert.alert("Confirm Delete", "Are you sure you want to remove this report from history?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            setIsDeleting(true);

            if (!report.request_id) throw new Error("Missing request_id");

            const token = await getCredentials ();

            const res = await fetch(
              `${API_CONFIG.baseUrl}/report/${report.request_id}`,
              {
                method: "DELETE",
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              }
            );

            if (!res.ok) throw new Error("Failed to delete report");

            Alert.alert("Deleted", "Report removed successfully");
          } catch (err: any) {
            Alert.alert("Error", err.message || "Could not delete report");
          } finally {
            setIsDeleting(false);
          }
        },
      },
    ]);
  };

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

      if (!report.request_id) {
        throw new Error("Missing request_id for PDF");
      }

      const token = await getCredentials ();

      const url = `${API_CONFIG.baseUrl}/report-pdf/${report.request_id}`;

      const fileUri = FileSystem.documentDirectory + `${report.request_id}.pdf`;

      const downloadRes = await FileSystem.downloadAsync(url, fileUri, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (downloadRes.status !== 200) {
        throw new Error("Failed to download PDF");
      }

      await Sharing.shareAsync(downloadRes.uri);
    } catch (err: any) {
      Alert.alert("Error", err.message || "Could not download PDF");
    } finally {
      setIsDownloading(false);
    }
  };

  const Section = ({ title, children }: any) => (
    <View style={styles.card}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );

  const BulletList = ({ items }: { items: string[] }) => (
    <View>
      {items.map((b, i) => (
        <Text key={i} style={styles.bullet}>
          • {b}
        </Text>
      ))}
    </View>
  );

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{report.title}</Text>

      <Text style={styles.subtitle}>
        {report.subtitle?.category} – {report.subtitle?.timeframe_reviewed}
      </Text>

      {report.image_url && (
        <Image
          source={{ uri: report.image_url }}
          style={{
            width: "100%",
            height: 200,
            borderRadius: 8,
            backgroundColor: "#15193a",
            marginBottom: 10,
          }}
          resizeMode="contain"
        />
      )}

      <Section title="Executive Summary">
        <BulletList items={report.executive_summary?.bullets || []} />
      </Section>

      <Section title="Risk Overview">
        <Text style={styles.highlight}>
          Overall Risk Level: {report.executive_summary?.overall_risk_level}
        </Text>
      </Section>

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

      <TouchableOpacity
        style={[styles.pdfButton, { backgroundColor: "#EF4444" }]}
        onPress={deleteReport}
        disabled={isDeleting}
      >
        {isDeleting ? (
          <ActivityIndicator color="white" />
        ) : (
          <>
            <MaterialCommunityIcons name="trash-can-outline" size={22} color="white" />
            <Text style={styles.pdfButtonText}>Remove from History</Text>
          </>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: "#333552", flexGrow: 1 },
  title: { fontSize: 24, fontWeight: "bold", color: "white", marginBottom: 16, textAlign: "center" },
  card: { backgroundColor: "#15193a", borderRadius: 16, padding: 16, marginBottom: 16 },
  sectionTitle: { color: "white", fontSize: 18, fontWeight: "bold", marginBottom: 8 },
  pdfButton: { backgroundColor: "#2563EB", paddingVertical: 16, borderRadius: 12, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 40 },
  pdfButtonText: { color: "white", fontSize: 18, fontWeight: "600" },
  subtitle: { color: "#b3b8e0", textAlign: "center", marginBottom: 12 },
  bullet: { color: "#b3b8e0", marginBottom: 6, fontSize: 14 },
  highlight: { color: "#4ade80", fontWeight: "bold", fontSize: 16 },
});
