import { Amplify } from 'aws-amplify'
import { fetchAuthSession, fetchUserAttributes, getCurrentUser, signInWithRedirect, signOut } from 'aws-amplify/auth'
import { cognitoUserPoolsTokenProvider } from 'aws-amplify/auth/cognito'

const config = import.meta.env
const userPoolId = config.VITE_COGNITO_USER_POOL_ID
const clientId = config.VITE_COGNITO_CLIENT_ID
const domain = config.VITE_COGNITO_DOMAIN
const callbackUrl = config.VITE_COGNITO_CALLBACK_URL
const logoutUrl = config.VITE_COGNITO_LOGOUT_URL

export const authConfigured = [userPoolId, clientId, domain, callbackUrl, logoutUrl]
  .every((value) => value && !value.toLowerCase().includes('replace-me'))

if (authConfigured) {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId: clientId,
        loginWith: {
          oauth: {
            domain: domain.replace(/^https?:\/\//, ''),
            scopes: ['openid', 'email', 'profile'],
            redirectSignIn: [callbackUrl],
            redirectSignOut: [logoutUrl],
            responseType: 'code',
          },
        },
      },
    },
  })
  cognitoUserPoolsTokenProvider.setKeyValueStorage(window.sessionStorage)
}

export async function getSignedInUser() {
  if (!authConfigured) return null
  try {
    const user = await getCurrentUser()
    const session = await fetchAuthSession()
    let email = session.tokens?.idToken?.payload?.email
    if (typeof email !== 'string' || !email) {
      email = (await fetchUserAttributes()).email
    }
    return { ...user, userId: user.userId, email: typeof email === 'string' ? email : null }
  } catch (error) {
    if (error?.name === 'UserUnAuthenticatedException') return null
    throw error
  }
}

export async function getAccessToken() {
  if (!authConfigured) return null
  const session = await fetchAuthSession()
  return session.tokens?.accessToken?.toString() || null
}

export function signIn() {
  return signInWithRedirect()
}

export function signOutUser() {
  return signOut()
}
