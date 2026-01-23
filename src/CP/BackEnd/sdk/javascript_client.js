// JavaScript client SDK for WAOOAW API

class WAOOAWClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/api/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        return response.json();
    }
}

// Example usage
const client = new WAOOAWClient("http://localhost:8015");
client.login("test@example.com", "password").then(console.log);
