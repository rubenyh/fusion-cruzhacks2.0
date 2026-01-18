import Auth0 from 'react-native-auth0';

const auth0 = new Auth0({
  domain: process.env.EXPO_PUBLIC_AUTH0_DOMAIN!,
  clientId: process.env.EXPO_PUBLIC_AUTH0_CLIENT_ID!,
});

export async function loginWithAuth0() {
  return auth0.webAuth.authorize({
    scope: 'openid profile email',
    audience: process.env.EXPO_PUBLIC_AUTH0_AUDIENCE,
  });
}

export default auth0;
