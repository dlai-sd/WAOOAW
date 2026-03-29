import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-links">
            <a href="/#about">About</a>
            <a href="/#blog">Blog</a>
            <a href="/#docs">Docs</a>
            <a href="/#support">Support</a>
            <Link to="/privacy">Privacy</Link>
            <Link to="/terms">Terms</Link>
          </div>
          <p className="footer-copyright">© 2026 WAOOAW. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
