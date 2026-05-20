import { useGoogleLogin } from "@react-oauth/google";

export default function GmailConnect({ onConnect }) {
  const login = useGoogleLogin({
    scope: "https://www.googleapis.com/auth/gmail.send",
    onSuccess: (tokenResponse) => {
      // Save access token to use when sending
      onConnect(tokenResponse.access_token);
    },
    onError: () => console.error("Gmail login failed"),
  });

  return (
    <button onClick={login} className="gmail-connect-btn">
      Connect Gmail
    </button>
  );
}