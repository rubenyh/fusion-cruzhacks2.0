import React, { useEffect, useState } from "react";
import { Modal, View, Text, ActivityIndicator, StyleSheet, TouchableOpacity } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";

interface TaskProgressModalProps {
  visible: boolean;
  onClose: () => void;
  requestId: string;
  apiBaseUrl: string;
  onComplete: (report: any) => void;
}

const TASKS = [
  { key: "detect", label: "Detect" },
  { key: "deep_search", label: "Deep Search" },
  { key: "writer", label: "Writer" },
];

type ProgressState = { [key: string]: boolean; detect: boolean; deep_search: boolean; writer: boolean };
export default function TaskProgressModal({ visible, onClose, requestId, apiBaseUrl, onComplete }: TaskProgressModalProps) {
  const [progress, setProgress] = useState<ProgressState>({ detect: false, deep_search: false, writer: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    let interval: ReturnType<typeof setInterval>;
    let isMounted = true;
    setLoading(true);
    setError(null);
    setProgress({ detect: false, deep_search: false, writer: false });

    const poll = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/reports`);
        if (!res.ok) throw new Error("Failed to poll status");
        const reports = await res.json();
        const report = Array.isArray(reports)
          ? reports.find((r: any) => r.request_id === requestId)
          : null;
        if (!report) return;
        // Simulate steps based on status/fields
        const detectDone = !!report.detection;
        const deepSearchDone = !!report.final_report && report.final_report.deep_search;
        const writerDone = report.status === "complete";
        if (isMounted) {
          setProgress({
            detect: detectDone,
            deep_search: deepSearchDone,
            writer: writerDone,
          });
        }
        if (writerDone) {
          clearInterval(interval);
          setTimeout(() => {
            if (isMounted) onComplete(report);
          }, 800);
        }
      } catch (e: any) {
        setError(e.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    };
    poll();
    interval = setInterval(poll, 2000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [visible, requestId]);

  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <Text style={styles.title}>Processing Report</Text>
          <View style={styles.tasks}>
            {TASKS.map((task, idx) => (
              <View key={task.key} style={styles.taskRow}>
                <View style={[styles.circle, progress[task.key] && styles.circleDone]}>
                  {progress[task.key] ? (
                    <MaterialCommunityIcons name="check" size={20} color="#fff" />
                  ) : (
                    <ActivityIndicator color="#fff" size="small" />
                  )}
                </View>
                <Text style={styles.taskLabel}>{task.label}</Text>
              </View>
            ))}
          </View>
          {error && <Text style={styles.error}>{error}</Text>}
          <TouchableOpacity style={styles.closeBtn} onPress={onClose} disabled={loading}>
            <Text style={styles.closeBtnText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modal: {
    backgroundColor: '#23244a',
    borderRadius: 16,
    padding: 28,
    width: 320,
    alignItems: 'center',
  },
  title: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 18,
  },
  tasks: {
    width: '100%',
    marginBottom: 18,
  },
  taskRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  circle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#44457a',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  circleDone: {
    backgroundColor: '#4ade80',
  },
  taskLabel: {
    color: '#fff',
    fontSize: 16,
  },
  error: {
    color: '#ff6b6b',
    marginTop: 8,
    marginBottom: 8,
  },
  closeBtn: {
    marginTop: 10,
    paddingVertical: 8,
    paddingHorizontal: 18,
    backgroundColor: '#44457a',
    borderRadius: 8,
  },
  closeBtnText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
