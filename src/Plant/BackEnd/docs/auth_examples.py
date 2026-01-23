"""
Authentication examples for WAOOAW Plant API in multiple languages.
"""

def python_auth_example():
    """
    Example of authentication in Python.
    """
    print("import requests")
    print("response = requests.post('http://localhost:8000/api/v1/auth/token', data={'username': 'user', 'password': 'pass'})")
    print("token = response.json().get('access_token')")

def javascript_auth_example():
    """
    Example of authentication in JavaScript.
    """
    print("fetch('http://localhost:8000/api/v1/auth/token', {")
    print("  method: 'POST',")
    print("  body: JSON.stringify({ username: 'user', password: 'pass' }),")
    print("  headers: { 'Content-Type': 'application/json' }")
    print("})")
    print("  .then(response => response.json())")
    print("  .then(data => console.log(data.access_token));")

def java_auth_example():
    """
    Example of authentication in Java.
    """
    print("import java.net.HttpURLConnection;")
    print("import java.net.URL;")
    print("import java.io.OutputStream;")
    print("URL url = new URL('http://localhost:8000/api/v1/auth/token');")
    print("HttpURLConnection conn = (HttpURLConnection) url.openConnection();")
    print("conn.setRequestMethod('POST');")
    print("conn.setDoOutput(true);")
    print("String jsonInputString = '{\"username\": \"user\", \"password\": \"pass\"}';")
    print("try (OutputStream os = conn.getOutputStream()) {")
    print("    byte[] input = jsonInputString.getBytes(\"utf-8\");")
    print("    os.write(input, 0, input.length);")
    print("}")

# Example usage
if __name__ == "__main__":
    python_auth_example()
    javascript_auth_example()
    java_auth_example()
