import React, { createContext, useContext, useEffect, useState } from 'react';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import * as SecureStore from 'expo-secure-store';

interface User {
  sub: string;
  name?: string;
  email?: string;
  picture?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getCredentials: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const auth0Domain = process.env.EXPO_PUBLIC_AUTH0_DOMAIN;
  const clientId = process.env.EXPO_PUBLIC_AUTH0_CLIENT_ID;
  const audience = process.env.EXPO_PUBLIC_AUTH0_AUDIENCE;
  const redirectUri = AuthSession.makeRedirectUri({ useProxy: true } as any);
console.log('Redirect URI:', redirectUri);

  useEffect(() => {
    (async () => {
      const token = await SecureStore.getItemAsync('accessToken');
      if (token) {
        setAccessToken(token);
        await fetchUserInfo(token);
      }
      setIsLoading(false);
    })();
  }, []);

  const fetchUserInfo = async (token: string) => {
    try {
      const response = await fetch(`https://${auth0Domain}/userinfo`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const info = await response.json();
        setUser({
          sub: info.sub,
          name: info.name,
          email: info.email,
          picture: info.picture,
        });
      }
    } catch (err) {
      console.error('Failed to fetch user info', err);
    }
  };

  const login = async () => {
    try {
      const request = new AuthSession.AuthRequest({
        clientId,
        scopes: ['openid', 'profile', 'email'],
        redirectUri,
        responseType: AuthSession.ResponseType.Token,
      });

    const result = await request.promptAsync({ authorizationEndpoint: `https://${auth0Domain}/authorize` });

    if (result.type === 'success' && result.params.access_token) {
  const token = result.params.access_token;
  await SecureStore.setItemAsync('accessToken', token);
  setAccessToken(token);
  await fetchUserInfo(token);
}
    } catch (err) {
      console.error('Login error', err);
    }
  };

  const logout = async () => {
    try {
      const logoutUrl = `https://${auth0Domain}/v2/logout?client_id=${clientId}&returnTo=${encodeURIComponent(redirectUri)}`;
      await WebBrowser.openBrowserAsync(logoutUrl);
    } catch (err) {
      console.error('Logout error', err);
    } finally {
      setUser(null);
      setAccessToken(null);
      await SecureStore.deleteItemAsync('accessToken');
    }
  };

  const getCredentials = async () => accessToken;

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout, getCredentials }}>
      {children}
    </AuthContext.Provider>
  );
};
