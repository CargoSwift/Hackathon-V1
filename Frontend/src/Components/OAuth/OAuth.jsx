import { useTheme } from '@mui/material/styles';
import { AppProvider } from '@toolpad/core/AppProvider';
import { SignInPage } from '@toolpad/core/SignInPage';
import * as React from 'react';

// Define all providers: Passkey + selected OAuth (GitHub & Google)
const providers = [
  { id: 'passkey', name: 'Passkey' },
  { id: 'github', name: 'GitHub' },
  { id: 'google', name: 'Google' },
];

// Handle sign-in logic
const signIn = async (provider) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      if (provider.id === 'passkey') {
        alert(`Signing up with ${provider.name}`);
        resolve(); // no error for passkey
      } else {
        console.log(`Sign in with ${provider.name}`);
        resolve({ error: 'This is a fake error for demo purposes.' });
      }
    }, 500);
  });
};

export default function CombinedSignInPage() {
  const theme = useTheme();
  return (
    <AppProvider theme={theme}>
      <SignInPage
        signIn={signIn}
        providers={providers}
        slotProps={{
          emailField: { autoFocus: false },
          form: { noValidate: true },
        }}
      />
    </AppProvider>
  );
}
