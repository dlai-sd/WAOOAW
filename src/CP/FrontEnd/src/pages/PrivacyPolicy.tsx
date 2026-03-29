import Footer from '../components/Footer'

export default function PrivacyPolicy() {
  return (
    <main className="legal-page" data-testid="legal-privacy-page">
      <section className="legal-hero">
        <div className="container legal-hero-content">
          <div className="legal-kicker">Privacy Policy</div>
          <h1>How WAOOAW handles customer data</h1>
          <p>
            WAOOAW helps businesses try, hire, and operate AI agents. This page explains what data we collect,
            why we collect it, how it is used, and what choices customers have.
          </p>
          <div className="legal-meta">Last updated: March 29, 2026</div>
        </div>
      </section>

      <section className="legal-section">
        <div className="container legal-card-stack">
          <article className="legal-card">
            <h2>1. What we collect</h2>
            <p>
              We collect information you provide directly, such as your name, email address, phone number,
              business name, business profile details, payment-related records, and any information you enter
              while hiring or configuring an agent.
            </p>
            <p>
              We also collect operational data needed to run the service, such as session activity, usage logs,
              billing status, agent setup details, and system events required for security, troubleshooting,
              and service improvement.
            </p>
          </article>

          <article className="legal-card">
            <h2>2. Connected platform data</h2>
            <p>
              If you connect a third-party account such as YouTube, WAOOAW accesses only the permissions you
              explicitly grant. For YouTube, this can include reading channel status, uploading videos, and
              managing video publishing actions that are part of the workflow you request.
            </p>
            <p>
              We use connected platform data only to provide the customer-requested service inside WAOOAW,
              such as showing connection status, drafting publishing actions, or executing approved uploads.
              We do not sell this connected-platform data.
            </p>
          </article>

          <article className="legal-card">
            <h2>3. How we use information</h2>
            <p>We use information to:</p>
            <ul>
              <li>Create and manage your account</li>
              <li>Match you with relevant AI agents and trials</li>
              <li>Operate connected-platform workflows you request</li>
              <li>Process billing, subscriptions, and support requests</li>
              <li>Protect the platform from fraud, abuse, and security incidents</li>
              <li>Improve product quality, reliability, and user experience</li>
            </ul>
          </article>

          <article className="legal-card">
            <h2>4. Legal basis and consent</h2>
            <p>
              We process personal information when it is necessary to provide the service you request, to comply
              with legal obligations, to protect the platform, or when you provide consent, including when you
              authorize a third-party connection.
            </p>
          </article>

          <article className="legal-card">
            <h2>5. Storage and security</h2>
            <p>
              WAOOAW uses technical and organisational safeguards designed to protect customer data. Sensitive
              credentials are stored server-side, access is restricted to authorized systems and personnel, and
              security logging is used to monitor misuse and incidents.
            </p>
            <p>
              No security system is perfect, but we work to reduce exposure through encryption, access controls,
              environment separation, and secure operational practices.
            </p>
          </article>

          <article className="legal-card">
            <h2>6. Sharing of information</h2>
            <p>
              We may share information with service providers who help us run the platform, such as hosting,
              authentication, analytics, payment, or communications providers, but only to the extent needed
              to deliver the WAOOAW service.
            </p>
            <p>
              We may also disclose information if required by law, regulation, legal process, or to enforce
              our rights and protect customers, partners, and the platform.
            </p>
          </article>

          <article className="legal-card">
            <h2>7. Retention and deletion</h2>
            <p>
              We retain information for as long as needed to provide the service, comply with legal obligations,
              resolve disputes, and maintain security and accounting records.
            </p>
            <p>
              If you want your account or connected-platform data deleted, contact us at
              <a href="mailto:privacy@waooaw.com"> privacy@waooaw.com</a>. We will review the request and delete
              or anonymize data where legally and operationally permitted.
            </p>
          </article>

          <article className="legal-card">
            <h2>8. Your choices</h2>
            <p>
              You can choose whether to create an account, whether to connect external platforms, and whether to
              continue using WAOOAW after a trial. You may also request access, correction, or deletion of certain
              personal information, subject to legal and security requirements.
            </p>
          </article>

          <article className="legal-card">
            <h2>9. Contact</h2>
            <p>
              For privacy questions, data requests, or complaints, contact
              <a href="mailto:privacy@waooaw.com"> privacy@waooaw.com</a>.
            </p>
          </article>
        </div>
      </section>

      <Footer />
    </main>
  )
}