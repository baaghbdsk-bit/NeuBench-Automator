import sys
import os
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REDIRECT_URI = "http://localhost:8585/callback"
CLIENT_ID = "77gvoxvtfcld9s"
CLIENT_SECRET = "WPL_AP1.hpz9c7e8fqQ6NzP6.klcQMw=="

auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body style='font-family:sans-serif;text-align:center;padding:50px;'><h2>LinkedIn Authorization Successful!</h2><p>You can close this tab now and return to your terminal.</p></body></html>")
        else:
            error = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h2>Authorization Failed</h2><p>{error}</p></body></html>".encode())

def run_oauth():
    global auth_code
    scopes = "w_member_social openid profile email"
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": "neubench_secure_state_123",
        "scope": scopes
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(params)}"
    
    print("\n" + "="*70)
    print("💼 LINKEDIN OFFICIAL OAUTH SETUP")
    print("="*70)
    print("\n1. Make sure you added this Redirect URL in your LinkedIn Developer App:")
    print(f"   --> {REDIRECT_URI} <--")
    print("   (Go to LinkedIn Developer Portal -> Your App -> Auth tab -> OAuth 2.0 settings -> Authorized redirect URLs)")
    print("\n2. Opening your browser to authorize access...")
    print(f"\nIf browser doesn't open, click this link manually:\n{auth_url}\n")
    
    webbrowser.open(auth_url)
    
    server = HTTPServer(("localhost", 8585), OAuthCallbackHandler)
    print("Waiting for callback on http://localhost:8585/callback ...")
    while not auth_code:
        server.handle_request()
        
    print("\nAuthorization code received!")
    print("Exchanging authorization code for permanent Access Token...")
    
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(token_url, data=payload, headers=headers)
    
    if r.status_code != 200:
        print(f"Failed to get token: {r.status_code} - {r.text}")
        return False
        
    token_data = r.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")
    print(f"Access Token generated successfully! (Valid for {int(expires_in)//86400} days)")
    
    # Get user URN (sub) via userinfo
    userinfo_url = "https://api.linkedin.com/v2/userinfo"
    u_resp = requests.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
    if u_resp.status_code == 200:
        u_data = u_resp.json()
        sub = u_data.get("sub")
        name = u_data.get("name")
        print(f"Connected LinkedIn Member: {name} (URN: urn:li:person:{sub})")
        person_urn = f"urn:li:person:{sub}"
    else:
        print("Fallback: checking /v2/me ...")
        me_resp = requests.get("https://api.linkedin.com/v2/me", headers={"Authorization": f"Bearer {access_token}"})
        sub = me_resp.json().get("id")
        person_urn = f"urn:li:person:{sub}"
        print(f"URN: {person_urn}")
        
    # Save to local .env
    with open(".env", "a", encoding="utf-8") as f:
        f.write(f"\nLINKEDIN_CLIENT_ID={CLIENT_ID}\n")
        f.write(f"LINKEDIN_CLIENT_SECRET={CLIENT_SECRET}\n")
        f.write(f"LINKEDIN_ACCESS_TOKEN={access_token}\n")
        f.write(f"LINKEDIN_PERSON_URN={person_urn}\n")
        
    print("\nCredentials saved to local .env file!")
    
    # Test posting
    print("\nTesting immediate live post via Official LinkedIn REST API...")
    test_text = "Building NeuBench: real-time AI latency & token drift benchmarks across 260+ LLMs. Live evals at https://app.neubench.workers.dev/ #AI #Tech"
    
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    post_payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": test_text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    p_resp = requests.post(
        post_url,
        json=post_payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
    )
    
    if p_resp.status_code in [200, 201]:
        print("SUCCESS! Post published to LinkedIn via Official API!")
        print(f"Response: {p_resp.json()}")
        return True, access_token, person_urn
    else:
        print(f"Test post returned status {p_resp.status_code}: {p_resp.text}")
        return False, access_token, person_urn

if __name__ == "__main__":
    run_oauth()
