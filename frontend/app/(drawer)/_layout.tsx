import { MaterialCommunityIcons } from "@expo/vector-icons";
import { DrawerActions } from "@react-navigation/native";
import * as Haptics from 'expo-haptics';
import { useNavigation, useRouter } from "expo-router";
import { Drawer } from "expo-router/drawer";
import { useState } from "react";
import { Dimensions, Platform, Pressable, StyleSheet, Switch, Text, TouchableOpacity, View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { useAuth } from "@/context/AuthContext";
const width = Dimensions.get("window").width;

const customTitles: Record<string, string> = {
  contact: "Contacto",
  faq: width <= 410 ? "FAQ" : "Preguntas Frecuentes",
  about: "Sobre Nosotros",
  "settings/index": "Configuración",
};

export default function Layout() {
  const router = useRouter();

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Drawer
        screenOptions={({ route }: { route: { name: string } }) => ({
          headerShown: Object.keys(customTitles).includes(route.name) || route.name === "actualizarDatos",
          title: customTitles[route.name] || (route.name === "actualizarDatos" ? "Actualizar Datos" : route.name),
          headerLeft: () => {
            if (route.name === "actualizarDatos") {
              return (
                <TouchableOpacity 
                  style={{ marginLeft: 10 }}
                  onPress={() => router.back()}
                >
                  <MaterialCommunityIcons name="arrow-left" size={24} color="#15193a" />
                </TouchableOpacity>
              );
            }
            return null; // Remove the drawer button from here since tabs handle it
          },
        })}
        drawerContent={() => <CustomDrawerContent />}
      />
    </GestureHandlerRootView>
  );
}

function CustomDrawerContent() {
  const router = useRouter();
  const { user, isAuthenticated, login, logout } = useAuth();
  const [isDarkMode, setIsDarkMode] = useState(false);

  const handleAuth = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      if (isAuthenticated) {
        await logout();
      } else {
        await login();
      }
    } catch (error) {
      console.error('Auth error:', error);
    }
  };

  const toggleTheme = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setIsDarkMode(previousState => !previousState);
  };

  const menuItems: { title: string; path: string }[] = [
    { title: "Home", path: '(tabs)/stackhome' },
  ];

  return (
    <View style={styles.drawerContainer}>
      <View style={styles.titleContainer}>
        <View style={styles.headerContainer}>
          <Text style={styles.titleText}>Menu</Text>
        </View>

        {isAuthenticated && user && (
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{user.name || 'User'}</Text>
            <Text style={styles.userEmail}>{user.email}</Text>
          </View>
        )}

        <View>
          <View style={styles.divider} />
          {menuItems.map((item, index) => (
            <View key={index}>
              <TouchableOpacity
                style={styles.menuItemContainer}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  router.navigate(item.path as any);
                }}
              >
                <Text style={styles.drawerItem}>{item.title}</Text>
              </TouchableOpacity>
              <View style={styles.dividerItems} />
            </View>
          ))}
        </View>
      </View>

      <Pressable
        onPress={handleAuth}
        style={({ pressed }) => [styles.logoutButton, pressed ? styles.logoutButtonPressed : {}]}
      >
        <MaterialCommunityIcons
          name={isAuthenticated ? 'logout' : 'login'}
          size={20}
          color="white"
        />
        <Text style={styles.logoutText}>
          {isAuthenticated ? 'Logout' : 'Log In / Sign Up'}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  drawerContainer: {
    flex: 1,
    padding: 24,
    justifyContent: "space-between",
    backgroundColor: "#333552",
  },
  titleContainer: {
    marginTop: 40,
  },
  headerContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  titleText: {
    fontSize: 24,
    fontWeight: "bold",
    color: "white",
    marginLeft: 0,
  },
  divider: {
    height: 1,
    backgroundColor: "#CCCCCC",
    marginVertical: 15,
  },
  dividerItems: {
    height: 1,
    backgroundColor: "#CCCCCC",
    marginVertical: 15,
  },
  themeContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 10,
  },
  themeTextContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  themeText: {
    fontSize: 16,
    fontWeight: "bold",
    color: "white",
    marginLeft: 15,
  },
  menuItemContainer: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    borderRadius: 8,
  },
  drawerItem: {
    fontSize: 16, 
    fontWeight: "bold", 
    color: "white", 
    marginLeft: 15,
  },
  logoutButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 12,
    borderRadius: 8,
    backgroundColor: "#15193a",
    justifyContent: "center",
  },
  logoutButtonPressed: {
    backgroundColor: "#202552",
  },
  logoutText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  userInfo: {
    paddingVertical: 16,
    paddingHorizontal: 8,
  },
  userName: {
    fontSize: 18,
    fontWeight: "bold",
    color: "white",
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: "#cccccc",
  },
});